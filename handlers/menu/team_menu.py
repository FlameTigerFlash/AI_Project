from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from llmbot import run_gigachat
from database.database import *
from handlers.ui import *
from handlers.states import *


router = Router()


async def team_menu(user_id:int, bot: Bot, state: FSMContext):
    await state.clear()
    await state.set_state(TeamManager.default_state)
    txt = await TextBlocks.get_team_menu()
    kb = await Keyboards.get_team_keyboard()
    await bot.send_message(user_id, txt, reply_markup=kb)


@router.callback_query(F.data=='team_menu')
async def cb_to_team_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await team_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=="create_team", TeamManager.default_state)
async def create_team(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, название команды.")
    await state.set_state(TeamManager.create_awaiting_name)


@router.message(F.text, TeamManager.create_awaiting_name)
async def create_set_team_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not (3 <= len(name) <= 25):
        await message.answer("Длина имени должна составлять от 3 до 25 символов.")
        return
    await message.answer("Введите, пожалуйста, пароль.")
    await state.update_data(table_name=name)
    await state.set_state(TeamManager.create_awaiting_password)


@router.message(F.text, TeamManager.create_awaiting_password)
async def create_set_team_password(message: Message, bot:Bot, state: FSMContext):
    password = message.text.strip()
    if not (5 <= len(password) <= 15):
        await message.answer("Длина пароля должна составлять от 5 до 15 символов.")
        return
    data = await state.get_data()
    author_data = await db_get_items(table='users', id=message.from_user.id)
    if len(author_data) != 1:
        await message.answer("К сожалению, вас нет в базе данных.")
        await team_menu(user_id=message.from_user.id, bot=bot, state=state)
        return
    exists = await db_element_exists(table='teams', name=data['table_name'])
    if exists:
        await message.answer("Команда с данным названием уже существует.")
        await team_menu(user_id=message.from_user.id, bot=bot, state=state)
        return
    await db_insert_element(table='teams', name=data['table_name'], password=password)
    await db_create_table(table=data['table_name'], id='INTEGER', name='VARCHAR(30)', admin='BOOLEAN')
    await db_insert_element(table=data['table_name'], id=message.from_user.id, name=author_data[0][1], admin="TRUE")
    await message.answer(f"Таблица команды {data['table_name']} создана.")
    await team_menu(user_id=message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=="join_team", TeamManager.default_state)
async def cb_join_team(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, название команды.")
    await state.set_state(TeamManager.join_awaiting_name)


@router.message(F.text, TeamManager.join_awaiting_name)
async def join_set_team_name(message: Message, state: FSMContext):
    team_name = message.text.strip()
    exists = await db_element_exists(table='teams', name=team_name)
    if not exists:
        await message.answer("Укажите, пожалуйста, название существующей команды.")
        return
    await state.update_data(team_name=team_name)
    await state.set_state(TeamManager.join_awaiting_password)
    await message.answer("Введите пароль.")


@router.message(F.text, TeamManager.join_awaiting_password)
async def join_set_team_password(message: Message, bot:Bot, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    author_data = await db_get_items(table='users', id=message.from_user.id)
    if len(author_data) != 1:
        await message.answer("К сожалению, вас нет в базе данных.")
        await team_menu(user_id=message.from_user.id, bot=bot, state=state)
        return
    member_already = await db_element_exists(table=data['team_name'], id=author_data[0][0])
    if member_already:
        await message.answer("Вы уже являетесь членом данной команды.")
        await team_menu(user_id=message.from_user.id, bot=bot, state=state)
        return
    exists = await db_element_exists(table='teams', name=data['team_name'], password=password)
    if not exists:
        await message.answer("Неверный пароль.")
        return
    await db_insert_element(table=data['team_name'], id=author_data[0][0], name=author_data[0][1], admin="FALSE")
    await message.answer("Вы были добавлены в команду!")
    await team_menu(user_id=message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='teams_list', TeamManager.default_state)
async def teams_list(callback:CallbackQuery, bot: Bot, state:FSMContext):
    teams = await db_get_items(table='teams')
    if len(teams) == 0:
        await bot.send_message(callback.from_user.id, "Список команд пуст. Вы можете создать собственную.")
        return
    txt = ""
    for el in teams:
        txt += f"{el[0]}. {el[1]}\n"
    await bot.send_message(callback.from_user.id, txt)


@router.callback_query(F.data=='team_members', TeamManager.default_state)
async def req_team_members(callback:CallbackQuery, bot: Bot, state:FSMContext):
    if not (await db_element_exists(table='teams')):
        await bot.send_message(callback.from_user.id, "На данный момент список команд пуст.")
        return
    await state.set_state(TeamManager.list_awaiting_name)
    await bot.send_message(callback.from_user.id, "Введите название интересующей вас команды.")


@router.message(F.text, TeamManager.list_awaiting_name)
async def show_team_members(message:Message, bot: Bot, state:FSMContext):
    team_name = message.text
    try:
        members = await db_get_items(table=team_name)
        txt = ""
        for member in members:
            txt += f"{"[ADMIN] " if member[2] == 'TRUE' else ""}{member[1]}\n"
        await bot.send_message(message.from_user.id, txt)
        await team_menu(user_id=message.from_user.id, bot=bot, state=state)
    except:
        await bot.send_message(message.from_user.id, "Введите, пожалуйста, корректное название команды.")

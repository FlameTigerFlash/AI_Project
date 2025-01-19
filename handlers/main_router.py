from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot
from handlers.states import *
from database.database import *
from handlers.ui import *
from handlers.menu.main_menu import main_menu, router as main_menu_router
from handlers.menu.team_menu import team_menu, router as team_menu_router
from handlers.menu.task_menu import task_menu, router as task_menu_router
from handlers.menu.task_editor_menu import task_editor_menu, router as task_editor_menu_router
from handlers.menu.cabinet_menu import cabinet_menu, router as cabinet_menu_router


router = Router()
router.include_router(main_menu_router)
router.include_router(team_menu_router)
router.include_router(task_menu_router)
router.include_router(task_editor_menu_router)
router.include_router(cabinet_menu_router)


async def back(user_id, bot:Bot, state: FSMContext):
    cur_state = await state.get_state()
    if cur_state in Form.__states__ or cur_state is None:
        await main_menu(user_id, bot, state)
    if cur_state in TeamManager.__states__:
        await team_menu(user_id, bot, state)
    if cur_state in TaskManager.__states__:
        await task_menu(user_id, bot, state)
    if cur_state in TaskEditor.__states__:
        await task_editor_menu(user_id, bot, state)
    if cur_state in Cabinet.__states__:
        await cabinet_menu(user_id, bot, state)

#Функция только для разработчика.
@router.message(Command("dev_info"))
async def dev_info(message:Message):
    rows = await db_get_items(table='communication')
    for row in rows:
        print(row)


@router.message(Command("clear"))
async def cmd_clear(message: Message, bot: Bot) -> None:
    try:
        for i in range(message.message_id, 0, -1):
            await bot.delete_message(message.from_user.id, i)
    except TelegramBadRequest:
        return


@router.message(Command("exit"))
async def exit_state(state: FSMContext) -> None:
    await state.clear()


@router.callback_query(F.data=="back")
async def cb_back(callback: CallbackQuery,bot:Bot, state: FSMContext):
    await back(callback.from_user.id,bot=bot, state=state)


@router.message(Command("back"))
async def cmd_back(message:Message, bot:Bot, state: FSMContext):
    await back(message.from_user.id, bot, state)


@router.message(Command("help"))
async def helper(message: Message, bot:Bot, state: FSMContext) -> None:
    txt = await TextBlocks.get_helper_menu()
    await message.answer(txt)
    await back(message.from_user.id, bot=bot, state=state)


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    data = await db_get_items(table='users', id=message.from_user.id)
    if len(data) == 0:
        await state.set_state(Form.waiting_for_nickname)
        await message.answer("Добрый день! Похоже, вы пользуетесь ботом впервые. Пожалуйста, введите свой никнейм.")
    else:
        await message.answer(f'Привет, {data[0][1]}! Вы уже зарегистрированы!')
        kb = await Keyboards.get_start_keyboard()
        text = await TextBlocks.get_main_menu()
        await message.answer(text, reply_markup=kb)


@router.message(F.text, Form.waiting_for_nickname)
async def insert_nickname(message:Message, state: FSMContext):
    nickname = message.text
    await db_insert_element(table='users', id=message.from_user.id, name=nickname, completed=0, failed=0)
    await message.answer(f'{nickname}! Вы зарегистрированы!')
    await state.clear()
    kb = await Keyboards.get_start_keyboard()
    text = await TextBlocks.get_main_menu()
    await message.answer(text, reply_markup=kb)


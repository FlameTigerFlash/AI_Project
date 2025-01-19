from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from database.database import *
from handlers.ui import *
from handlers.states import *
from langchain_core.messages import HumanMessage, AIMessage
from llmbot import run_gigachat
import os
from dotenv import load_dotenv


router = Router()


async def cabinet_menu(user_id:int, bot: Bot, state: FSMContext):
    await state.clear()
    await state.set_state(Cabinet.default_state)
    txt = await TextBlocks.get_cabinet_menu()
    kb = await Keyboards.get_cabinet_keyboard()
    await bot.send_message(user_id, txt, reply_markup=kb)


@router.callback_query(F.data=='cabinet_menu')
async def cb_to_cabinet_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await cabinet_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='get_current_tasks')
async def get_current_tasks(callback:CallbackQuery, bot: Bot, state:FSMContext):
    tasks = await db_get_employee_tasks(user_id=callback.from_user.id)
    if not tasks:
        return 'На данный момент активных задач нет.'
    resp = ""
    for row in tasks:  # Проходим по всем строкам
        if row[5] != 'IN_PROCESS':
            continue
        resp += (f"ID: {row[0]}, Название: {row[2]},\nКоманда: {row[3]}\n Описание: {row[4]}\n "
                 f"Роль: {row[6]}\n"
                 f"Статус: {row[5]}\n")
    await bot.send_message(callback.from_user.id, text=(resp if len(resp) else "На данный момент активных задач нет."))
    await cabinet_menu(callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='get_stats')
async def get_stats(callback:CallbackQuery, bot: Bot, state:FSMContext):
    tasks = await db_get_employee_tasks(user_id=callback.from_user.id)
    user = (await db_get_items(table='users', id=callback.from_user.id))[0]
    txt = f"Статистика пользователя: выполнено - {user[2]}, провалено - {user[3]}. "
    if user[2] + user[3] != 0:
        txt += f"Процент выполнения: {user[2]/(user[2]+user[3])*100}%\n"
    failed_tasks = []
    completed_tasks = []
    for task in tasks:
        task_id, task_director_id, task_name, task_team, task_description, task_status, user_tasks_role, review_comment, users_estimation_comment = task[:9]
        if task_status == 'IN_PROCESS':
            continue
        elif task_status == 'ВЫПОЛНЕНО':
            completed_tasks.append((task_id, task_director_id, task_name, task_description, review_comment, users_estimation_comment))
        else:
            failed_tasks.append((task_id, task_director_id, task_name, task_description, review_comment, users_estimation_comment))
    txt += 'Выполненные задачи:\n'
    for el in completed_tasks:
        txt += (f"Задача {el[0]}: {el[2]}\n"
                f"Описание: {el[3]}\n"
                f"Ваш отзыв: {el[4]}\n")
        if callback.from_user.id != el[1]:
            txt += f"Отзыв руководителя о Вас: {el[5]}\n"
    txt += 'Проваленные задачи:\n'
    for el in failed_tasks:
        txt += (f"Задача {el[0]}: {el[2]}\n"
                f"Описание: {el[3]}\n"
                f"Ваш отзыв: {el[4]}\n")
        if callback.from_user.id != el[1]:
            txt += f"Отзыв руководителя о Вас: {el[5]}\n"
    await bot.send_message(callback.from_user.id, text=txt)
    await cabinet_menu(callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='get_notifications')
async def get_notifications(callback:CallbackQuery, bot: Bot, state:FSMContext):
    notifications = await db_get_notifications(callback.from_user.id)
    directors_requests = [el for el in notifications if el[2] == 'Запрос']
    managers_answers = [el for el in notifications if el[2] == 'Ответ']
    outcoming_requests = [el for el in notifications if el[2] == 'Исходящий']
    txt = ""
    txt += "Запросы руководителей задач, требующие Вашего ответа:\n"
    for el in directors_requests:
        txt += f"Задача {el[0]}: {el[1]}\nТекст запроса: {el[3]}\n"
    txt += "Ответы от назначенных Вами Менеджеров:\n"
    for el in managers_answers:
        txt += f"Задача {el[0]}: {el[1]}\nОтвет: {el[3]}\n"
    txt += "Исходящие запросы менеджерам:\n"
    for el in outcoming_requests:
        txt += f"Задача {el[0]}: {el[1]}\nОтвет: {el[3]}\n"
    await state.set_state(Cabinet.checking_notifications)
    await bot.send_message(callback.from_user.id, text=txt)
    kb = await Keyboards.get_notifications_keyboard()
    txt = await TextBlocks.get_notifications_menu()
    await bot.send_message(callback.from_user.id, text=txt, reply_markup=kb)


@router.callback_query(F.data=='answer_notification')
async def answer_notification(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите номер (ID) задачи.")
    await state.set_state(Cabinet.choosing_task)


@router.message(F.text, Cabinet.choosing_task)
async def choose_task(message:Message, state:FSMContext):
    task_id = message.text
    try:
        task_id = int(task_id)
        exists = await db_element_exists(table='communication', task_id=task_id, type='Запрос', resolved='FALSE')
        if not exists:
            await message.answer("Активного запроса по данной задаче не существует.")
            return
        is_manager = await db_element_exists(table='user_tasks', user_id=message.from_user.id, task_id=task_id, role='Менеджер')
        if not is_manager:
            await message.answer("Вы не являетесь менеджером данной задачи.")
            return
        await message.answer("Введите текст ответа.")
        await state.set_state(Cabinet.setting_reply)
        await state.update_data(task_id=task_id)
    except:
        await message.answer("Введён некорретный ID задачи.")


@router.message(F.text, Cabinet.setting_reply)
async def set_reply(message:Message, bot:Bot, state:FSMContext):
    txt = message.text
    data = await state.get_data()
    await db_update_element(table='communication', where= {'task_id':data['task_id'], 'type':'Запрос', 'resolved':'FALSE'}, resolved='TRUE')
    await db_insert_element(table='communication', task_id = data['task_id'], type='Ответ', body=txt, resolved='FALSE')
    kb = await Keyboards.get_notifications_keyboard()
    await state.clear()
    try:
        task = (await db_get_items(table='tasks', id=data['task_id']))[0]
        await bot.send_message(task[1], f"Получен ответ по заданию {data['task_id']}!")
    except:
        await message.answer("Не получилось найти руководителя задачи.")
    await message.answer('Ответ доставлен! Меню к Вашим услугам!', reply_markup=kb)
    await state.set_state(Cabinet.choosing_task)


@router.callback_query(F.data=='read_all_notifications')
async def read_all_notifications(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await db_clear_notifications(user_id=callback.from_user.id)
    await bot.send_message(callback.from_user.id, "Уведомления очищены.")


@router.callback_query(F.data=='get_ai_self_review')
async def get_ai_self_review(callback:CallbackQuery, bot:Bot, state:FSMContext):
    system_prompt = (f"Ты являешься экспертом в области управления задачами и организации командной работы,"
                     f" при анализе делающим упор на статистику и способным обнаружить сильные и слабые места стратегии.")
    tasks = await db_get_employee_tasks(user_id=callback.from_user.id)
    if len(tasks) == 0:
        await bot.send_message(callback.from_user.id, "Завершённых задач нет.")
        return
    if len(tasks) > 5:
        tasks = tasks[len(tasks)-5:]
    txt = ("Проанализируй, пожалуйста, мою статистику, мои выполненные и проваленные задачи и дай рекомендации для будущей работы."
           "Список задач:\n")
    for task in tasks:
        task_id, task_director_id, task_name, task_team, task_description, task_status, user_tasks_role, review_comment, users_estimation_comment = task[:9]
        if task_status == 'IN_PROCESS':
            continue
        txt += (f"Задача {task_id} - {task_name}\n"
                f"Описание: {task_description}\n"
                f"Задание {task_status.capitalize()}\n"
                f"Роль участника: {user_tasks_role}\n"
                f"Отзыв участника: {review_comment}\n")
        if callback.from_user.id != task_director_id:
            txt += f"Комментарий руководителя об участнике: {users_estimation_comment}\n"
    load_dotenv()
    gigachat_key = os.getenv("GIGA_CHAT_KEY")
    dialogue = [HumanMessage(txt)]
    #print(txt)
    await bot.send_message(callback.from_user.id, "Анализ в процессе...")
    response = await run_gigachat(gigachat_key=gigachat_key, dialogue_messages=dialogue, system_message_content=system_prompt, max_history_length=2)
    await bot.send_message(callback.from_user.id, response)
    await cabinet_menu(callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='fill_out_form')
async def fill_out_form(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Как здорово, что Вы решили поделиться впечатлениями!"
                                                  "Введите, пожалуйста, комментарий (при необходимости он будет замещён)!")
    await state.set_state(Cabinet.filling_form)


@router.message(F.text, Cabinet.filling_form)
async def insert_form_comment(message:Message, bot:Bot, state:FSMContext):
    txt = message.text
    await db_delete_element(table='form', user_id=message.from_user.id)
    await db_insert_element(table='form', user_id=message.from_user.id, comment=txt)
    await message.answer("Спасибо за Ваш отзыв! Вы помогаете улучшать систему!")
    await cabinet_menu(message.from_user.id, bot=bot, state=state)
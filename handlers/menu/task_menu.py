from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
import os
from dotenv import load_dotenv
from handlers.ui import *
from handlers.states import *
from langchain_core.messages import HumanMessage, AIMessage
from llmbot import run_gigachat
from database.database import *


load_dotenv()
gigachat_key = os.getenv("GIGA_CHAT_KEY")


router = Router()


async def task_menu(user_id:int, bot: Bot, state: FSMContext):
    await state.clear()
    await state.set_state(TaskManager.default_state)
    txt = await TextBlocks.get_task_menu()
    kb = await Keyboards.get_task_keyboard()
    await bot.send_message(user_id, txt, reply_markup=kb)


@router.callback_query(F.data=='task_menu')
async def cb_to_task_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await task_menu(user_id=callback.from_user.id, bot=bot, state=state)


async def get_tasks(user_id:int)->str:
    tasks = await db_get_employee_tasks(user_id=user_id)
    if not tasks:
        return 'На данный момент активных задач нет.'
    resp = ""
    for row in tasks:  # Проходим по всем строкам
        resp += (f"ID: {row[0]}, NAME: {row[2]},\nTEAM: {row[3]}\n DESCRIPTION: {row[4]}\n "
                 f"ROLE:{row[6]}\n"
                 f"STATUS: {row[5]}\n")
    return resp


async def add_tasks(state: FSMContext)->str:
    await state.set_state(TaskManager.setting_task_team)
    return "Введите название команды(team), в которой будет реализована данная задача."


@router.message(F.text, TaskManager.setting_task_team)
async def set_task_team(message: Message, state: FSMContext):
    team_name = message.text.strip()
    exists = await db_element_exists(table='teams', name=team_name)
    if not exists:
        await message.answer("Команды с данным названием не существует.")
        return
    try:
        is_admin = await db_element_exists(table=team_name, id=message.from_user.id, admin='TRUE')
    except Exception:
        await message.answer("Вы не принадлежите к числу руководителей данной команды.")
        return
    if not is_admin:
        await message.answer("Вы не принадлежите к числу руководителей данной команды.")
        return
    await message.answer("Введите, пожалуйста, название задачи.")
    await state.update_data(team_name=team_name)
    await state.set_state(TaskManager.setting_task_name)


@router.message(F.text, TaskManager.setting_task_name)
async def set_task_name(message: Message, state: FSMContext):
    task_name_buffer = message.text.strip().split(";")
    if len(task_name_buffer) == 0:
        await message.answer("Введите, пожалуйста, корректные названия задач.")
        return
    await message.answer("Введите исполнителей задач. (разделитель ;)")
    await state.update_data(names = task_name_buffer)
    await state.set_state(TaskManager.setting_task_user)


@router.message(F.text, TaskManager.setting_task_user)
async def set_task_user(message: Message, bot:Bot, state: FSMContext):
    data = await state.get_data()
    users = message.text.split(";")
    if len(users) == 0:
        await message.answer("Введите, пожалуйста, корректные имена пользователей.")
        return
    async with aiosqlite.connect('users.db') as db:
        for name in data["names"]:
            valid_users = []
            for user in users:
                user_ids = await db_get_items(table=data['team_name'], name=user)
                if len(user_ids) != 1:

                    await message.answer(f'Пользователь {user} не найден в базе данных')
                    continue
                valid_users.append(user)

            if len(valid_users) == 0:
                await message.answer("Введите, пожалуйста, имена присутствующих в команде пользователей.")
                return
            await db_insert_element(table='tasks', director_id=message.from_user.id, name=name.strip(), executors=";".join(valid_users), team=data['team_name'], status="IN_PROCESS")
            await db.commit()
            last = await db_get_items(table='tasks', director_id=message.from_user.id, name=name.strip())
            last = last[-1]
            #print(last)
            task_id = last[0]
            await db.execute('INSERT INTO user_tasks (user_id, role, task_id) VALUES (?, ?, ?)',
                             (message.from_user.id, 'Директор', task_id))
            for ind,user in enumerate(valid_users):  # добавляем каждого пользователя
                user_ids = await db_get_items(table='users', name=user)  # получаем все user_id
                user_id = user_ids[0][0]
                #print(user_id, task_id)
                if user_id != message.from_user.id:
                    await db.execute('INSERT INTO user_tasks (user_id, role, task_id) VALUES (?, ?, ?)',
                                 (user_id, 'Исполнитель', task_id))

        await db.commit()
    await message.answer("Задачи успешно добавлены!")
    await task_menu(user_id=message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='add_tasks', TaskManager.default_state)
async def cb_add_tasks(callback:CallbackQuery, bot: Bot, state:FSMContext):
    text = await add_tasks(state)
    await bot.send_message(callback.from_user.id, text)


@router.message(Command("add_tasks"), TaskManager.default_state)
async def txt_add_tasks(message: Message, state: FSMContext):
    text = await add_tasks(state)
    await message.answer(str(text))


@router.callback_query(F.data=='get_tasks', TaskManager.default_state)
async def cb_get_tasks(callback:CallbackQuery, bot: Bot):
    text = await get_tasks(callback.from_user.id)
    await bot.send_message(callback.from_user.id, text)


@router.message(Command("get_tasks"), TaskManager.default_state)
async def txt_get_tasks(message: Message):
    text = await get_tasks(message.from_user.id)
    await message.answer(str(text))


@router.callback_query(F.data=="write_review", TaskManager.default_state)
async def write_review(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, ID задачи для отзыва.")
    await state.set_state(TaskManager.setting_review_id)


@router.message(F.text, TaskManager.setting_review_id)
async def set_review_id(message: Message, state:FSMContext):
    try:
        await state.update_data(task_id=int(message.text))
    except:
        await message.answer("Введите, пожалуйста, корректное число.")
        return
    is_member = await db_element_exists(table='user_tasks', user_id=int(message.from_user.id), task_id=int(message.text))
    #rows = await db_get_items(table='user_tasks')
    #print(rows)
    if not is_member:
        await message.answer("Вы не являетесь исполнителем данной задачи.")
        return
    await state.set_state(TaskManager.setting_review_comment)
    await message.answer("Введите, пожалуйста, текст вашего отзыва. Если отзыв уже существует, он будет удалён и замещён.")


@router.message(F.text, TaskManager.setting_review_comment)
async def set_review_comment(message: Message, bot:Bot, state:FSMContext):
    txt = message.text
    data = await state.get_data()
    await db_delete_element(table='review', task_id=data['task_id'], user_id=message.from_user.id)
    await db_insert_element(table='review', task_id=data['task_id'], user_id=message.from_user.id, comment=txt)
    await message.answer("Отзыв успешно добавлен!")
    await task_menu(user_id=message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='task_editor_menu')
async def cb_select_task(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.clear()
    await state.set_state(TaskManager.selecting_task)
    await bot.send_message(callback.from_user.id, "Выберите, пожалуйста, номер интересующей задачи.")


@router.callback_query(F.data=='ai_review')
async def ai_review(callback:CallbackQuery, bot: Bot, state:FSMContext):
    user_id = callback.from_user.id
    tasks = await db_get_employee_tasks(user_id=user_id)
    finished_tasks = await db_get_items(table='completion_log')
    finished_tasks = [task[0] for task in finished_tasks]
    tasks = [task for task in tasks if task[0] in finished_tasks and task[1] == user_id]
    if len(tasks) == 0:
        await bot.send_message(user_id, "Завершённых задач на данный момент нет.")
        return
    dialogue = []
    system_prompt = (f"Ты являешься экспертом в области управления задачами и организации командной работы,"
                     f" при анализе делающим упор на статистику и способным обнаружить сильные и слабые места стратегии.")
    txt = (f"Проанализируй, пожалуйста, статистику за прошедший отчётный период "
           f"и при необходимости дай рекомендации как для руководителя заданий (директора),"
           f"так и для сотрудников (менеджеров и исполнителей)."
           f"Я буду предоставлять тебе информацию о каждой задаче, проанализируй их по отдельности."
           f"Когда я попрошу подвести итоги, суммаризируй свои отчёты, укажи на сильные и слабые места участников "
           f"и дай им рекомендации.")
    dialogue.append(HumanMessage(content=txt))
    response = await run_gigachat(gigachat_key=gigachat_key, system_message_content=system_prompt,
                                  dialogue_messages=dialogue, max_history_length=3)
    dialogue.append(AIMessage(content=response))
    worker_names = set()
    for task in tasks:
        txt = ""
        #print(task)
        task_id, task_name, task_description, task_status = task[0], task[2], task[4], task[5]
        workers = await db_get_task_employees(task_id=task_id)
        txt += f"Название задачи: {task_name}\n"
        txt += f"Описание задачи: {task_description}\n"
        txt += f"Задание {"провалено" if task_status != 'ВЫПОЛНЕНО' else 'выполнено успешно'}.\n"
        txt += f"Сотрудники, работавшие над задачей:\n"
        for worker in workers:
            worker_name, worker_role, worker_comment = worker[1], worker[4], worker[5]
            worker_names.add(worker_name)
            txt += f"{worker_name}: {worker_role}. "
            if worker_comment is None:
                txt += f"Без отзыва\n"
            else:
                txt += f"Отзыв: {worker_comment}"
        comms = await db_get_items(table='communication', task_id=task_id)
        txt += "Коммуникация по задаче (директора с командой):\n"
        for msg in comms:
            msg_type, body = msg[1], msg[2]
            txt += "Директор: " if msg_type == 'Запрос' else "Команда: "
            txt += f"{body}\n"
        #print(txt)
        dialogue.append(HumanMessage(content=txt))
        await bot.send_message(user_id, f"Анализируем задачу {task[0]}...")
        response = await run_gigachat(gigachat_key=gigachat_key, system_message_content=system_prompt,
                                      dialogue_messages=dialogue, max_history_length=3)
        await bot.send_message(user_id, text=response)
        dialogue.append(AIMessage(content=response))

    await bot.send_message(user_id, f"Подводим итоги...")
    txt = (f"Подведи, пожалуйста, итоги по разобранным выше задачам, предоставь отчёт о завершённых задачах,а именно:\n"
           f"{";\n".join([task[2] for task in tasks])};\n"
           f"дай рекомендации сотрудникам:\n"
           f"{";\n".join([worker_name for worker_name in worker_names])}.")
    #print(txt)
    dialogue.append(HumanMessage(txt))
    response = await run_gigachat(gigachat_key=gigachat_key, system_message_content=system_prompt,
                                  dialogue_messages=dialogue, max_history_length=3)
    await bot.send_message(user_id, text=response)
    await task_menu(user_id=callback.from_user.id, bot=bot, state=state)
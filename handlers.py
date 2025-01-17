from aiogram import Router, F
from aiogram.filters import CommandStart, Command, CommandObject
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.exceptions import TelegramBadRequest
from aiogram import Bot
from datetime import datetime
import os
from dotenv import load_dotenv
from langchain_core.messages import SystemMessage, HumanMessage, AIMessage

from llmbot import run_gigachat
from states import *
from database import *
from ui import *


load_dotenv()
gigachat_key = os.getenv("GIGA_CHAT_KEY")

router = Router()


@router.message(Command("dev_info"))
async def dev_info(message: Message):
    rows = await db_get_task_employees(1)
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
async def exit_state(message: Message, state: FSMContext) -> None:
    await state.clear()


@router.message(Command("back"))
async def back(state: FSMContext):
    cur_state = await state.get_state()
    if cur_state in Form.__states__:
        await state.clear()
    if cur_state in TeamManager.__states__:
        await state.clear()
        await state.set_state(TeamManager.default_state)
    if cur_state in TaskManager.__states__:
        await state.clear()
        await state.set_state(TaskManager.default_state)
    if cur_state in TaskEditor.__states__:
        await state.set_state(TaskEditor.default_state)


@router.callback_query(F.data=="back")
async def cb_back(callback: CallbackQuery, state: FSMContext):
    await back(state)


@router.message(Command("help"))
async def helper(message: Message, state: FSMContext) -> None:
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Текущие задачи", callback_data="get_tasks"),
         InlineKeyboardButton(text="Добавить задачи", callback_data="add_tasks")]
    ])
    await message.answer(
        "Представляем Вашему вниманию интерфейс бота \"Team Scheduler\"\n"
        "Бот предоставляет возможности для поставления задач, отслеживания их выполнения, "
        "анализа статистики и получения рекомендаций.",
    reply_markup=keyboard)


@router.message(Command("start"), State(None))
async def cmd_start(message: Message, state: FSMContext):
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


async def get_tasks(user_id:int)->str:
    controlled_tasks = await db_get_items(table='tasks', director_id=user_id)
    if not controlled_tasks:
        return 'На данный момент активных задач нет.'
    resp = ""
    for row in controlled_tasks:  # Проходим по всем строкам
        resp += (f"ID: {row[0]}, NAME: {row[2]},\nTEAM: {row[3]}\n DESCRIPTION: {row[5]}\n "
                 f"EXECUTORS:\n {"\n".join(row[4].split(";"))}\n"
                 f"STATUS: {row[6]}\n")
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
    except:
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
async def set_task_user(message: Message, state: FSMContext):
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
    await back(state)


@router.callback_query(F.data=='add_tasks', TaskManager.default_state)
async def cb_add_tasks(callback:CallbackQuery, bot: Bot, state:FSMContext):
    text = await add_tasks(state)
    await bot.send_message(callback.from_user.id, text)


@router.message(Command("add_tasks"), TaskManager.default_state)
async def txt_add_tasks(message: Message, state: FSMContext):
    text = await add_tasks(state)
    await message.answer(str(text))


@router.callback_query(F.data=='get_tasks', TaskManager.default_state)
async def cb_get_tasks(callback:CallbackQuery, bot: Bot, state:FSMContext):
    text = await get_tasks(callback.from_user.id)
    await bot.send_message(callback.from_user.id, text)


@router.message(Command("get_tasks"), TaskManager.default_state)
async def txt_get_tasks(message: Message, state: FSMContext):
    text = await get_tasks(message.from_user.id)
    await message.answer(str(text))


@router.callback_query(F.data=="write_review", TaskManager.default_state)
async def write_review(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, ID задачи для фидбека.")
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
async def set_review_comment(message: Message, state:FSMContext):
    txt = message.text
    data = await state.get_data()
    await db_delete_element(table='review', task_id=data['task_id'], user_id=message.from_user.id)
    await db_insert_element(table='review', task_id=data['task_id'], user_id=message.from_user.id, comment=txt)
    await state.clear()
    await state.set_state(TaskManager.default_state)
    await message.answer("Отзыв успешно добавлен!")


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
async def create_set_team_password(message: Message, state: FSMContext):
    password = message.text.strip()
    if not (5 <= len(password) <= 15):
        await message.answer("Длина пароля должна составлять от 5 до 15 символов.")
        return
    data = await state.get_data()
    author_data = await db_get_items(table='users', id=message.from_user.id)
    if len(author_data) != 1:
        await message.answer("К сожалению, вас нет в базе данных.")
        await back(message, state)
        return
    exists = await db_element_exists(table='teams', name=data['table_name'])
    if exists:
        await message.answer("Команда с данным названием уже существует.")
        await back(message, state)
        return
    await db_insert_element(table='teams', name=data['table_name'], password=password)
    await db_create_table(table=data['table_name'], id='INTEGER', name='VARCHAR(30)', admin='BOOLEAN')
    await db_insert_element(table=data['table_name'], id=message.from_user.id, name=author_data[0][1], admin="TRUE")
    await message.answer(f"Таблица команды {data['table_name']} создана.")
    await state.clear()
    await state.set_state(TeamManager.default_state)


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
async def join_set_team_password(message: Message, state: FSMContext):
    password = message.text.strip()
    data = await state.get_data()
    author_data = await db_get_items(table='users', id=message.from_user.id)
    if len(author_data) != 1:
        await message.answer("К сожалению, вас нет в базе данных.")
        await back(message, state)
        return
    member_already = await db_element_exists(table=data['team_name'], id=author_data[0][0])
    if member_already:
        await message.answer("Вы уже являетесь членом данной команды.")
        await back(message, state)
        return
    exists = await db_element_exists(table='teams', name=data['team_name'], password=password)
    if not exists:
        await message.answer("Неверный пароль.")
        return
    await db_insert_element(table=data['team_name'], id=author_data[0][0], name=author_data[0][1], admin="FALSE")
    await message.answer("Вы были добавлены в команду!")
    await state.clear()
    await state.set_state(TeamManager.default_state)


@router.callback_query(F.data=="get_workers")
async def get_workers(callback:CallbackQuery, bot: Bot, state:FSMContext):
    data = await state.get_data()
    items = [(worker[0], worker[1]) for worker in await db_get_items(table='user_tasks', task_id=data['task_id'])]
    txt = ""
    for item in items:
        name = (await db_get_items(table='users', id=item[0]))[0][1]
        txt += f"{name} - {item[1]}\n"
    await bot.send_message(callback.from_user.id, txt)


@router.callback_query(F.data=="alter_task_status",TaskEditor.default_state)
async def alter_task_status(callback:CallbackQuery, bot: Bot, state:FSMContext):
    data = await state.get_data()
    tasks = await db_get_items(table='tasks', id = data['task_id'])
    if len(tasks) != 1 or tasks[0][6].strip() != 'IN_PROCESS':
        await bot.send_message(callback.from_user.id, "Задача отсутствует или уже завершена.")
        return
    await state.set_state(TaskEditor.alter_task_status)
    kb = await Keyboards.get_task_completion_keyboard()
    await bot.send_message(callback.from_user.id, "После выполнения задачу больше нельзя будет изменить.",
                           reply_markup=kb)


@router.callback_query(F.data=="task_completed", TaskEditor.alter_task_status)
async def task_completed(callback:CallbackQuery, bot: Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='tasks', where={'id': data['task_id']}, status='ВЫПОЛНЕНО')
    await db_insert_element(table='completion_log', task_id=data['task_id'])
    await db_finish_task(data['task_id'], success=True)
    await bot.send_message(callback.from_user.id, "Задача выполнена! Отлично!")
    await state.set_state(TaskEditor.default_state)


@router.callback_query(F.data=="task_failed", TaskEditor.alter_task_status)
async def task_failed(callback:CallbackQuery, bot: Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='tasks', where={'id': data['task_id']}, status='ПРОВАЛЕНО')
    await db_insert_element(table='completion_log', task_id=data['task_id'])
    await db_finish_task(data['task_id'], success=False)
    await bot.send_message(callback.from_user.id, "Задача провалена! Ничего страшного!")
    await state.set_state(TaskEditor.default_state)


@router.callback_query(F.data=="alter_worker_status",TaskEditor.default_state)
async def alter_worker_status(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.set_state(TaskEditor.choosing_worker)
    await bot.send_message(callback.from_user.id, "Введите никнейм работника.")


@router.message(F.text, TaskEditor.choosing_worker)
async def choose_worker(message:Message, state:FSMContext):
    data = await state.get_data()
    workers = await db_get_items(table='users', name=message.text)
    if len(workers) != 1 or not (await db_element_exists(table='user_tasks', user_id=workers[0][0], task_id=data['task_id'])):
        await message.answer("Данного пользователя нет в списке участников проекта.")
        return
    if (await db_get_items(table='user_tasks', user_id=workers[0][0], task_id=data['task_id']))[0][1] == 'Директор':
        await message.answer("Данный пользователь уже является директором задачи.")
        return
    await state.update_data(user_id=workers[0][0])
    await state.set_state(TaskEditor.choosing_role)
    kb  = await Keyboards.get_worker_status_keyboard()
    await message.answer("Выберите, пожалуйста, роль участника проекта.", reply_markup=kb)


@router.callback_query(F.data=="set_manager", TaskEditor.choosing_role)
async def set_manager(callback:CallbackQuery, bot:Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='user_tasks', where={'user_id':data['user_id'], 'task_id':data['task_id']}, role='Менеджер')
    await bot.send_message(callback.from_user.id, "Сотрудник назначен менеджером.")
    await state.set_state(TaskEditor.default_state)


@router.callback_query(F.data=="set_executor", TaskEditor.choosing_role)
async def set_executor(callback:CallbackQuery, bot:Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='user_tasks', where={'user_id':data['user_id'], 'task_id':data['task_id']}, role='Исполнитель')
    await bot.send_message(callback.from_user.id, "Сотрудник назначен исполнителем.")
    await state.set_state(TaskEditor.default_state)


@router.callback_query(F.data=="change_task_description", TaskEditor.default_state)
async def change_description(callback:CallbackQuery, bot:Bot, state:FSMContext):
    data = await state.get_data()
    await state.set_state(TaskEditor.changing_description)
    await bot.send_message(callback.from_user.id, "Введите описание задачи.")


@router.message(F.text, TaskEditor.changing_description)
async def insert_description(message:Message, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='tasks', where={'id':data['task_id']}, description=message.text)
    await state.set_state(TaskEditor.changing_description)
    await state.set_state(TaskEditor.default_state)
    await message.answer("Описание изменено.")


@router.callback_query(F.data=='main_menu')
async def to_main_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.clear()
    txt = await TextBlocks.get_main_menu()
    kb = await Keyboards.get_start_keyboard()
    await bot.send_message(callback.from_user.id, txt, reply_markup=kb)


@router.callback_query(F.data=='team_menu')
async def to_team_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.clear()
    await state.set_state(TeamManager.default_state)
    txt = await TextBlocks.get_team_menu()
    kb = await Keyboards.get_team_keyboard()
    await bot.send_message(callback.from_user.id, txt, reply_markup=kb)


@router.callback_query(F.data=='task_menu')
async def to_task_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.clear()
    await state.set_state(TaskManager.default_state)
    txt = await TextBlocks.get_task_menu()
    kb = await Keyboards.get_task_keyboard()
    await bot.send_message(callback.from_user.id, txt, reply_markup=kb)


@router.callback_query(F.data=='task_editor_menu')
async def select_task(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await state.clear()
    await state.set_state(TaskManager.selecting_task)
    await bot.send_message(callback.from_user.id, "Выберите, пожалуйста, номер интересующей задачи.")


@router.message(F.text, TaskManager.selecting_task)
async def to_task_edit_menu(message: Message, state: FSMContext):
    id = int(message.text)
    items = await db_get_items(table='tasks', id=id)
    if len(items) != 1:
        await message.answer("Такой задачи не существует.")
        return
    if items[0][1] != message.from_user.id:
        await message.answer("Вы не являетесь владельцем данной задачи.")
        return
    await state.set_state(TaskEditor.default_state)
    await state.update_data(task_id=id)
    txt = await TextBlocks.get_task_editor_menu()
    kb = await Keyboards.get_task_editor_keyboard()
    await message.answer(txt, reply_markup=kb)


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
    system_prompt = (f"Ты являешься экспертом в области управления задачами и организации командной работы,"
                     f" при анализе делающим упор на статистику и способным обнаружить сильные и слабые места стратегии.")
    txt = (f"Проанализируй, пожалуйста, статистику за прошедший отчётный период "
           f"и при необходимости дай рекомендации как для руководителя заданий (директора),"
           f"так и для сотрудников (менеджеров и исполнителей).\n")
    for task in tasks:
        #print(task)
        task_id, task_name, task_description, task_status = task[0], task[2], task[4], task[5]
        workers = await db_get_task_employees(task_id=task_id)
        txt += f"Название задачи: {task_name}\n"
        txt += f"Описание задачи: {task_description}\n"
        txt += f"Задание {"провалено" if task_status != 'ВЫПОЛНЕНО' else 'выполнено успешно'}.\n"
        txt += f"Сотрудники, работавшие над задачей:\n"
        for worker in workers:
            worker_name, worker_role, worker_comment = worker[1], worker[4], worker[5]
            txt += f"{worker_name}: {worker_role}. "
            if worker_comment is None:
                txt += f"Без отзыва\n"
            else:
                txt += f"Отзыв: {worker_comment}"
    #print(txt)
    dialogue = []
    history = await db_get_items(table='prompts', user_id=user_id)
    for prompt in history:
        status, text = prompt[1], prompt[2]
        if status == 'AIMessage':
            dialogue.append(AIMessage(content=text))
        elif status == 'HumanMessage':
            dialogue.append(HumanMessage(content=text))
    dialogue.append(HumanMessage(content=txt))
    await bot.send_message(user_id, "Анализ в процессе...")
    response = await run_gigachat(gigachat_key=gigachat_key, system_message_content=system_prompt,
                       dialogue_messages=dialogue, max_history_length=6)
    await db_insert_element(table='prompts', user_id=user_id, type='HumanMessage', body=txt)
    await db_insert_element(table='prompts', user_id=user_id, type='AIMessage', body=response)
    await bot.send_message(user_id, response)
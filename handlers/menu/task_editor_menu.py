from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram import Bot
from database.database import *
from handlers.ui import *
from handlers.states import *


router = Router()


async def task_editor_menu(user_id:int, bot: Bot, state: FSMContext):
    await state.set_state(TaskEditor.default_state)
    txt = await TextBlocks.get_task_editor_menu()
    kb = await Keyboards.get_task_editor_keyboard()
    await bot.send_message(user_id, txt, reply_markup=kb)


@router.message(F.text, TaskManager.selecting_task)
async def cb_to_task_editor_menu(message: Message, bot:Bot, state: FSMContext):
    task_id = int(message.text)
    items = await db_get_items(table='tasks', id=task_id)
    if len(items) != 1:
        await message.answer("Такой задачи не существует.")
        return
    if items[0][1] != message.from_user.id:
        await message.answer("Вы не являетесь владельцем данной задачи.")
        return
    await state.update_data(task_id=task_id)
    await task_editor_menu(user_id=message.from_user.id, bot=bot, state=state)


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
    await task_editor_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=="task_failed", TaskEditor.alter_task_status)
async def task_failed(callback:CallbackQuery, bot: Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='tasks', where={'id': data['task_id']}, status='ПРОВАЛЕНО')
    await db_insert_element(table='completion_log', task_id=data['task_id'])
    await db_finish_task(data['task_id'], success=False)
    await bot.send_message(callback.from_user.id, "Задача провалена! Ничего страшного!")
    await task_editor_menu(user_id=callback.from_user.id, bot=bot, state=state)


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
    await task_editor_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=="set_executor", TaskEditor.choosing_role)
async def set_executor(callback:CallbackQuery, bot:Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='user_tasks', where={'user_id':data['user_id'], 'task_id':data['task_id']}, role='Исполнитель')
    await bot.send_message(callback.from_user.id, "Сотрудник назначен исполнителем.")
    await task_editor_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=="change_task_description", TaskEditor.default_state)
async def change_description(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await state.set_state(TaskEditor.changing_description)
    await bot.send_message(callback.from_user.id, "Введите описание задачи.")


@router.message(F.text, TaskEditor.changing_description)
async def insert_description(message:Message, bot:Bot, state:FSMContext):
    data = await state.get_data()
    await db_update_element(table='tasks', where={'id':data['task_id']}, description=message.text)
    await message.answer("Описание изменено.")
    await task_editor_menu(user_id=message.from_user.id, bot=bot, state=state)
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


@router.callback_query(F.data=="send_request", TaskEditor.default_state)
async def send_request(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, текст запроса. "
                                                  "Если активный запрос существует, он будет замещён.")
    await state.set_state(TaskEditor.setting_request_text)


@router.message(F.text, TaskEditor.setting_request_text)
async def insert_request_text(message:Message, bot:Bot, state:FSMContext):
    data = await state.get_data()
    body = message.text
    exists = await db_element_exists(table='communication', task_id=data['task_id'], type='Запрос', resolved='FALSE')
    if exists:
        await db_update_element(table='communication', where={'task_id':data['task_id'],'type':'Запрос', 'resolved':'FALSE'}, body=body)
    else:
        await db_insert_element(table='communication', task_id=data['task_id'],  type = 'Запрос', resolved = 'FALSE', body=body)
    await message.answer("Запрос успешно добавлен!")
    workers = await db_get_task_employees(task_id=data['task_id'])
    for worker in workers:
        if worker[4] == 'Менеджер':
            await bot.send_message(worker[0], f'Получен запрос касательно задания {data['task_id']} '
                                              f'Подробнее можете посмотреть в своём личном кабинете.')
    await task_editor_menu(message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='get_reviews')
async def get_reviews(callback:CallbackQuery, bot:Bot, state:FSMContext):
    data = await state.get_data()
    members = await db_get_task_employees(task_id=data['task_id'])
    txt = ""
    for el in members:
        if el[5] is None:
            continue
        txt += f"Никнейм: {el[1]}, роль: {el[4]}\nОтзыв:{el[5]}\n"
    if len(txt) == 0:
        txt = "На данный момент отзывов нет."
    await bot.send_message(callback.from_user.id, text=txt)
    await task_editor_menu(callback.from_user.id,  bot=bot, state=state)


@router.callback_query(F.data=='estimate_member')
async def estimate_member(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await state.set_state(TaskEditor.choosing_estimated_member)
    await bot.send_message(callback.from_user.id, "Введите, пожалуйста, никнейм участника.")


@router.message(F.text, TaskEditor.choosing_estimated_member)
async def insert_estimated_member(message:Message, state:FSMContext):
    data = await state.get_data()
    workers = await db_get_items(table='users', name=message.text)
    if len(workers) != 1 or not (
    await db_element_exists(table='user_tasks', user_id=workers[0][0], task_id=data['task_id'])):
        await message.answer("Данного пользователя нет в списке участников проекта.")
        return
    if (await db_get_items(table='user_tasks', user_id=workers[0][0], task_id=data['task_id']))[0][1] == 'Директор':
        await message.answer("Данный пользователь является директором задачи.")
        return
    await state.update_data(user_id = workers[0][0])
    await state.set_state(TaskEditor.setting_member_comment)
    await message.answer("Введите комментарий о сотруднике (по возможности он заместит имеющийся).")


@router.message(F.text, TaskEditor.setting_member_comment)
async def insert_member_comment(message:Message, bot:Bot, state:FSMContext):
    data = await state.get_data()
    comment = message.text
    await db_delete_element(table='users_estimation', user_id=data['user_id'], task_id=data['task_id'])
    await db_insert_element(table='users_estimation', user_id=data['user_id'], task_id=data['task_id'], comment=comment)
    await message.answer("Комментарий успешно добавлен.")
    await task_editor_menu(message.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='add_new_workers')
async def add_new_workers(callback:CallbackQuery, bot:Bot, state:FSMContext):
    await state.set_state(TaskEditor.setting_new_members)
    await bot.send_message(callback.from_user.id,"Введите исполнителей задачи. (разделитель ;)")


@router.message(F.text, TaskEditor.setting_new_members)
async def set_new_members(message:Message, bot:Bot, state:FSMContext):
    data = await state.get_data()
    members = message.text.split(";")
    if len(members) == 0:
        await message.answer("Введите, пожалуйста, корректные имена пользователей.")
        return
    team_name = (await db_get_items(table='tasks', id=data['task_id']))[0][3]
    cnt = 0
    for member in members:
        user_ids = await db_get_items(table=team_name, name=member)
        if len(user_ids) != 1:
            await message.answer(f"Пользователь с никнеймом {member} не найден в списке команды.")
            continue
        user_id = user_ids[0][0]
        await db_insert_element(table='user_tasks', user_id=user_id, task_id=data['task_id'], role='Исполнитель')
        cnt += 1
    await message.answer(f"Количество добавленных участников: {cnt}.")
    await task_editor_menu(message.from_user.id, bot=bot, state=state)
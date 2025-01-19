from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup


class Form(StatesGroup):
    waiting_for_nickname = State()


class TaskManager(StatesGroup):
    default_state = State()
    setting_task_team = State()
    setting_task_name = State()
    setting_task_user = State()
    setting_review_id = State()
    setting_review_comment = State()
    selecting_task = State()


class TeamManager(StatesGroup):
    default_state = State()
    create_awaiting_name = State()
    create_awaiting_password = State()
    join_awaiting_name = State()
    join_awaiting_password = State()
    leave_awaiting_password  = State()
    delete_awaiting_name = State()
    list_awaiting_name = State()


class TaskEditor(StatesGroup):
    default_state = State()
    alter_task_status = State()
    choosing_worker = State()
    choosing_role = State()
    changing_description = State()
    setting_request_text = State()


class Cabinet(StatesGroup):
    default_state = State()
    checking_notifications = State()
    choosing_task = State()
    setting_reply = State()
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram import Bot
import os
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage
from llmbot import run_gigachat
from database.database import *
from handlers.ui import *
from handlers.states import *


load_dotenv()
gigachat_key = os.getenv("GIGA_CHAT_KEY")
router = Router()


async def main_menu(user_id:int, bot: Bot, state: FSMContext):
    await state.clear()
    txt = await TextBlocks.get_main_menu()
    kb = await Keyboards.get_start_keyboard()
    await bot.send_message(user_id, txt, reply_markup=kb)


@router.callback_query(F.data=='main_menu')
async def cb_to_main_menu(callback:CallbackQuery, bot: Bot, state:FSMContext):
    await main_menu(user_id=callback.from_user.id, bot=bot, state=state)


@router.callback_query(F.data=='help')
async def cb_help(callback:CallbackQuery, bot: Bot):
    kb = await Keyboards.get_start_keyboard()
    txt = await TextBlocks.get_helper_menu()
    await bot.send_message(callback.from_user.id, txt, reply_markup=kb)


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
    await main_menu(user_id=callback.from_user.id, bot=bot, state=state)
from aiogram import Bot
from database import *


async def task_reminder(bot: Bot):
    user_rows = await db_get_items(table='users')
    for user_row in user_rows:
        participation = await db_get_items(table='user_tasks', user_id=user_row[0])
        if len(participation)  == 0:
            continue
        txt = f"Добрый день! Ваши активные задания:\n"
        for el in participation:
            task = await db_get_items(table='tasks', id=el[2])
            task = task[0]
            if task[6].strip() != 'IN_PROCESS':
                continue
            txt += (f"ID: {el[2]};\n"
                    f"Название: {task[2]},"
                    f"Команда: {task[3]},"
                    f"Исполнители: {task[4]},"
                    f"Описание: {task[5]},"
                    f"Ваша роль: {el[1]}")
        await bot.send_message(user_row[0], text=txt)
import asyncio
import nest_asyncio
import logging
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram import BaseMiddleware
from aiogram.client.default import DefaultBotProperties
from typing import Any, Awaitable, Callable, Dict
from aiogram.types import TelegramObject, Update
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from aiogram.fsm.storage.memory import MemoryStorage
from handlers.main_router import router
from apsched import *
from database.database import *
from handlers.states import Form


nest_asyncio.apply()
load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")

logging.basicConfig(force=True, level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)


class SomeMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        fsm_context = data.get('state')
        try:
            state = await fsm_context.get_state()
            #print(f"Текущее состояние: {state}")
        except Exception as ex:
            print(ex)
            return
        if data['event_update'].message.text != '/start' and state != Form.waiting_for_nickname:
            chat_id = data['event_update'].message.chat.id
            async with aiosqlite.connect('users.db') as db:
                async with db.execute("SELECT id FROM users WHERE id = ?", (chat_id,)) as cursor:
                    if await cursor.fetchone() is None:
                        await bot.send_message(chat_id=chat_id, text='Вы не зарегистрированы! Зарегистрируйтесь, используя команду /start.')
                        return
        command = data['event_update'].message.text
        user_id = data['event_update'].message.from_user.id
        await db_insert_element(table='command_log', user_id=user_id, command=command)
        result = await handler(event, data)
        return result


async def main(): #Основная асинхронная функция, которая будет запускаться при старте бота.
    dp.message.outer_middleware(SomeMiddleware())
    scheduler = AsyncIOScheduler(timezone='Europe/Moscow')
    job = scheduler.add_job(task_reminder, trigger='cron', hour = 12, minute = 00, kwargs={'bot':bot})
    scheduler.start()
    dp.startup.register(start_db)
    try:
        print("Бот запущен...")
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.remove_job(job.id)
        await bot.session.close()
        print("Бот остановлен")


if __name__ == "__main__":
    asyncio.run(main())
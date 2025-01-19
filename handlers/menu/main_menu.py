from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram import Bot
from handlers.ui import *
from handlers.states import *


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
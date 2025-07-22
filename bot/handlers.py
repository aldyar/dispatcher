from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.state import Chat

user = Router()


@user.message(CommandStart())
async def cmd_start(message:Message):
    await message.answer(
    "*Привет! Я аналитик по лидам. Спроси — кто лучший, кто провалился, где эффективность выше.*\n\n"
    "*Я быстро всё проверю и дам тебе ясный ответ 💡*", parse_mode='Markdown')
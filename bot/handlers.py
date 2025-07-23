from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from bot.state import Chat
import bot.keyboards as kb
from function.operator_function import OperatorFunction
from function.tiktoken_function import TiktokenFunction
from function.category_function import CategoryFunction
from app.generator import send_to_openai
from app.category_list import LAW_CATEGORIES

user = Router()

@user.message(F.text == '❌Отмена')
@user.message(CommandStart())
async def cmd_start(message:Message,state:FSMContext):
    await state.clear()
    await message.answer(
    "*Привет! Я аналитик по лидам. Спроси — кто лучший, кто провалился, где эффективность выше.*\n\n"
    "*Я быстро всё проверю и дам тебе ясный ответ 💡*", parse_mode='Markdown',reply_markup=kb.main_menu)

@user.message(F.text == '💬 Чат с аналитиком')
async def chat_handler(message:Message,state:FSMContext):
    await state.set_state(Chat.chat)
    await message.answer('*Введите пожалуйста ваш запрос*',parse_mode='Markdown',reply_markup=kb.cancel)

@user.message(Chat.chat)
async def chatting_handlers(message:Message,state:FSMContext):
    await state.set_state(Chat.wait)

    response = message.text
    data = await CategoryFunction.generate_compact_stats_text()
    ai_response = await send_to_openai(data, response)
    tokens = await TiktokenFunction.async_count_tokens(data)
    print(f"Токенов: {tokens}")
    print(len(data))
    await message.answer(ai_response ,parse_mode='Markdown')
    await state.set_state(Chat.chat)
    

@user.message(Chat.wait)
async def cancel_chat(message:Message):
    await message.answer("⏳ Я всё ещё обрабатываю твой предыдущий запрос. Пожалуйста, подожди.")


@user.message(F.text == '📖 Инструкция')
async def instruction_handler(message:Message):
    await message.answer(
    "*🧠 Как работает Dispatcher:*\n\n"
    "📅 *Каждую неделю в понедельник в 03:00 ночи* программа автоматически выполняет задачу:\n\n"
    "— Получает операторов из CRM из таблицы пользователей, где роль = 3\n"
    "— Сохраняет их имена и ID\n"
    "— Загружает все лиды за последние 3 месяца\n"
    "— Стерилизует данные, чтобы избежать конфликтов\n"
    "— Сортирует лиды по ID операторов и делит на батчи (порции для ИИ)\n"
    "— Отправляет каждый батч в OpenAI (gpt-3.5/gpt-4), чтобы определить категорию\n"
    "— Категория определяется на основе заранее заготовленного списка\n"
    "— Сохраняет категории и все лиды в локальной БД\n"
    "— Строит статистику по 3 периодам: за 3 месяца, 1 месяц и 1 неделю\n\n"
    "⏱️ Задача выполняется *раз в неделю*, занимает ~30–45 минут. Запускается ночью — в неактивное время\n\n"
    "🔄 *Каждые 5 минут* программа проверяет, какие операторы находятся в онлайне через CRM\n\n"
    "*🤖 Telegram-бот:* можно задавать вопросы в свободной форме, например:\n"
    "— Кто самый эффективный оператор?\n"
    "— Кто лучший в определённой категории?\n"
    "— Статистика за 3 месяца, месяц или неделю\n\n"
    "📨 Также доступен API-роут `assign-lead` — ты отправляешь туда заявку, а в ответ получаешь *ID наиболее подходящего оператора*,\n"
    "исходя из категории лида и собранной статистики 📊",
    parse_mode='Markdown'
)
    

@user.message(F.text == '👥 Список операторов')
async def operators_list(message:Message):
    operators = await OperatorFunction.get_all_operators()

    if not operators:
        await message.answer("❌ Операторы не найдены.")
        return

    text = "*📋 Список операторов:*\n\n"
    for op in operators:
        text += f"— *{op.name}* (`ID: {op.operator_id}`)\n"

    await message.answer(text, parse_mode="Markdown")


@user.message(F.text == '📂 Список категорий')
async def categories_list(message: Message):
    text = "*📚 Список юридических категорий:*\n\n"
    for i, cat in enumerate(LAW_CATEGORIES, start=1):
        text += f"{i}. {cat}\n"

    await message.answer(text, parse_mode="Markdown")

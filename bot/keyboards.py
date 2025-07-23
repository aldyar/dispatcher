from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = '💬 Чат с аналитиком'),
                                           KeyboardButton(text = '📖 Инструкция')],
                                          [KeyboardButton(text = '📂 Список категорий'),
                                           KeyboardButton(text = '👥 Список операторов')]],resize_keyboard=True)


cancel = ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text = '❌Отмена')]],resize_keyboard=True)
import asyncio
from aiogram import Bot, Dispatcher
from config import TOKEN
from bot.handlers import user


async def main():
    bot = Bot(token = TOKEN)
    dp = Dispatcher()
    dp.include_routers(user)
    dp.startup.register(on_startup)
    await dp.start_polling(bot)


async def on_startup():
    print('✅BOT STARTED')


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
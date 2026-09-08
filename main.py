import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

import db
from config import config
from handlers.bot_funcs import router as bot_funcs_router
from handlers.callback import router as callback_router
from handlers.commands import router as commands_router
from handlers.inline import router as inline_router

dp = Dispatcher()


async def main() -> None:
    bot = Bot(
        token=config.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp.startup.register(db.on_startup)
    dp.shutdown.register(db.on_shutdown)
    dp.include_routers(commands_router, inline_router, callback_router, bot_funcs_router)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

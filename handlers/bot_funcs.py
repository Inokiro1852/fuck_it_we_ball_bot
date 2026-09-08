from aiogram import F, Router
from aiogram.types import Message

router = Router()

@router.message(F.text)
async def fixing_twitter_links(message: Message):
    message_text = message.text
    if "https://x.com" in message_text:
        message_text = message_text.replace('x.com', 'girlcockx.com')
        await message.reply(message_text)
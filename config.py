import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv('.env')


@dataclass
class Config:
    bot_token: str
    dump_chat_id: int


config = Config(
    bot_token=os.environ.get('BOT_TOKEN'),
    dump_chat_id=int(os.environ.get('DUMP_CHAT_ID'), 0),
)

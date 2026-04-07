import asyncio
import re
import sqlite3
from os import path

import aiosqlite
import requests

# imgURL = "https://static.wikia.nocookie.net/tmnt/images/b/b0/Set1-4-260-WayNinja-Tcard.png/revision/latest?cb=20230201183924"
#
# img_data = requests.get(imgURL).content
# with open('img/image_name.png', 'wb') as handler:
#     handler.write(img_data)

conn = sqlite3.connect('tmnt.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
cur.execute('''
AlTER TABLE cards_glued RENAME TO cards_glued_1
''')
# cur.execute('''INSERT INTO cards (card_number, name, strength, agility, fighting, brains, image_url)
#                VALUES (?, ?, ?, ?, ?, ?, ?)''',
#             ('175/260', 'Shredder', '9500', '9500', '9700', '9700',
#              'AgACAgIAAxkBAAIFJGnVc0AWtoe-CZOGX7BDavBtrNoXAAKIFWsblLWwSmYkMbblXJsaAQADAgADeQADOwQ'))
# row = cur.fetchall()
conn.commit()

# async def fetch_card(card_number: str, *columns: str):
#     if not columns:
#         columns = ("image_url",)
#     for column in columns:
#         if not column.isidentifier():
#             raise ValueError(f'Column "{column}" is not a valid identifier')
#
#     columns_str = ", ".join(columns)
#     async with aiosqlite.connect("tmnt.db") as db:
#         db.row_factory = aiosqlite.Row
#         async with db.execute(
#                 f'SELECT {columns_str} FROM cards WHERE card_number = ?', (card_number,)
#         ) as cursor:
#             return await cursor.fetchone()
#
# def is_image_url_exists(card_number: str):
#     card = asyncio.run(fetch_card(card_number))
#     if card is None:
#         return False
#     return True
#
# def get_local_img_path(card_number: str):
#     card = asyncio.run(fetch_card(card_number, 'name'))
#     card_name = f'img/{card['name']}.png'
#     return card_name
#
# def _sync_create_glued_wrap():
#     print(is_image_url_exists('0/260'))
#
# _sync_create_glued_wrap()

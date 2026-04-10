import asyncio
import os
import re
import sqlite3
import time
from os import path
from PIL import Image

import aiosqlite
import requests
from aiosqlite import cursor

conn = sqlite3.connect('tmnt.db')
conn.row_factory = sqlite3.Row
cur = conn.cursor()
# cur.execute('''
# DELETE FROM cards_abilities_1;
# ''')
# cur.execute('''INSERT INTO cards (card_number, name, strength, agility, fighting, brains, image_url)
#                VALUES (?, ?, ?, ?, ?, ?, ?)''',
#             ('175/260', 'Shredder', '9500', '9500', '9700', '9700',
#              'AgACAgIAAxkBAAIFJGnVc0AWtoe-CZOGX7BDavBtrNoXAAKIFWsblLWwSmYkMbblXJsaAQADAgADeQADOwQ'))
# row = cur.fetchall()
# conn.commit()

# list_img = os.listdir('img/cards_1')
# for img in list_img[47:]:
#     with Image.open(f'img/cards_1/{img}') as image:
#         name = img.split('.png')[0]
#         cur.execute('''
#         SELECT strength, agility, fighting, brains FROM cards_1 WHERE name = ?
#         ''', (name,))
#         card = cur.fetchone()
#         print(f'{name}: {card["strength"]} {card["agility"]} {card["fighting"]} {card["brains"]}')
#         image.show()
#         cin = input()
#         if not cin:
#             print(cin)
#             continue
#         else:
#             abilities = cin.split(' ')
#             strength = abilities[0]
#             agility = abilities[1]
#             fighting = abilities[2]
#             brains = abilities[3]
#             cur.execute('''
#             UPDATE cards_1 SET strength = ?, agility = ?, fighting = ?, brains = ? WHERE name = ?
#             ''', (strength, agility, fighting, brains, name))
#             conn.commit()

test1 = '3/260'
space = test1.split(' ')
print(space)


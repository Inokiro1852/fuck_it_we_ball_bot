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
import random

# conn = sqlite3.connect('tmnt.db')
# conn.row_factory = sqlite3.Row
# cur = conn.cursor()
# cur.execute('''
# DELETE FROM cards_abilities_1;
# ''')
# cur.execute('''INSERT INTO cards (card_number, name, strength, agility, fighting, brains, image_url)
#                VALUES (?, ?, ?, ?, ?, ?, ?)''',
#             ('175/260', 'Shredder', '9500', '9500', '9700', '9700',
#              'AgACAgIAAxkBAAIFJGnVc0AWtoe-CZOGX7BDavBtrNoXAAKIFWsblLWwSmYkMbblXJsaAQADAgADeQADOwQ'))
# row = cur.fetchall()
# conn.commit()

# TARGET_WIDTH = 660
# TARGET_HEIGHT = 920

# def standardise_images(source_dir, target_dir):
#     if not os.path.exists(target_dir):
#         os.makedirs(target_dir)
#     img_list = os.listdir(source_dir)
#     for img in img_list:
#         print(f'Processing image {img}')
#         source_path = os.path.join(source_dir, img)
#         target_path = os.path.join(target_dir, img)

#         with Image.open(source_path) as image:
#             if image.size != (TARGET_WIDTH, TARGET_HEIGHT):
#                 resized_img = image.resize((TARGET_WIDTH, TARGET_HEIGHT), Image.Resampling.LANCZOS)
#                 resized_img.save(target_path, 'PNG')
#             else:
#                 image.save(target_path, 'PNG')

# standardise_images('img/cards_abilities_1', 'img/cards_abilities_1_test')

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


def calculate_duel_result(p1: dict, p2: dict):
    win1 = 0
    win2 = 0
    stats_text = ''
    attributes = ['Strength', 'Agility', 'Fighting', 'Brains']

    for p in [p1, p2]:
        if len(p['cards']) == 2:
            abil = p['cards'][1]['card']
            if abil['target'] == 'any' or abil['effect_type'] == 'block':
                mutable_abil = dict(abil)
                mutable_abil['target'] = random.choice(attributes).lower()
                p['cards'][1]['card'] = mutable_abil

    for attribute in attributes:
        p1_val = p1['cards'][0]['card'][attribute.lower()]
        p2_val = p2['cards'][0]['card'][attribute.lower()]

        def apply_ability(ability, val_1, val_2, attr):
            eff_1 = ''
            eff_2 = ''
            if not ability or ability['target'] not in ['all', attr]:
                return val_1, val_2, eff_1, eff_2

            effect_type = ability['effect_type']
            effect_value = ability['effect_value']

            if effect_type == 'block':
                val_2 = 0
            elif effect_type == 'buff':
                val_1 += effect_value
                eff_1 = f'[+{effect_value}]'
            elif effect_type == 'debuff':
                val_2 -= effect_value
                eff_2 = f'[-{effect_value}]'

            return val_1, val_2, eff_1, eff_2

        p1_abil = p1['cards'][1]['card'] if len(p1['cards']) > 1 else None
        p2_abil = p2['cards'][1]['card'] if len(p2['cards']) > 1 else None

        eff_on_p1_str = ''
        eff_on_p2_str = ''

        p1_val, p2_val, eff_on_p1, eff_on_p2 = apply_ability(
            p1_abil, p1_val, p2_val, attribute.lower()
        )

        if eff_on_p1:
            eff_on_p1_str += f'{eff_on_p1}'
        if eff_on_p2:
            eff_on_p2_str += f'{eff_on_p1}'

        p2_val, p1_val, eff_on_p2, eff_on_p1 = apply_ability(
            p2_abil, p2_val, p1_val, attribute.lower()
        )

        if eff_on_p2:
            eff_on_p1_str += f'{eff_on_p2}'
        if eff_on_p1:
            eff_on_p2_str += f'{eff_on_p1}'

        if p1_val > p2_val:
            win1 += 1
            symbol = '&gt;'
        elif p1_val < p2_val:
            win2 += 1
            symbol = '&lt;'
        else:
            symbol = '='
        stats_text += (
            f'<i>{attribute}: {p1_val}{eff_on_p1} {symbol} {p2_val}{eff_on_p2}</i>\n'
        )


calculate_duel_result()
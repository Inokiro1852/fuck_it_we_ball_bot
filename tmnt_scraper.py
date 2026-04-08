from os import path

import requests
from bs4 import BeautifulSoup
import sqlite3
import time
import re
import cloudscraper

conn = sqlite3.connect('tmnt.db')
cur = conn.cursor()
# cur.execute('''
#             CREATE TABLE IF NOT EXISTS cards
#             (
#                 id
#                 INTEGER
#                 PRIMARY
#                 KEY
#                 AUTOINCREMENT,
#                 card_number
#                 TEXT
#                 NOT
#                 NULL,
#                 name
#                 TEXT
#                 NOT
#                 NULL,
#                 strength
#                 INTEGER
#                 NOT
#                 NULL,
#                 agility
#                 INTEGER
#                 NOT
#                 NULL,
#                 fighting
#                 INTEGER
#                 NOT
#                 NULL,
#                 brains
#                 INTEGER
#                 NOT
#                 NULL,
#                 image_url
#                 TEXT
#                 NOT
#                 NULL
#             )
#             ''')
conn.commit()

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5"
}

BASE_URL = "https://turtlepedia.fandom.com"
MAIN_URL = "https://turtlepedia.fandom.com/wiki/Teenage_Mutant_Ninja_Turtles:_Way_of_the_Ninja"


def get_high_res_img(img_url):
    clean_url = re.sub(r'/revision.*', '', img_url)
    return clean_url


def scrape_cards():
    scraper = cloudscraper.create_scraper()

    response = scraper.get(MAIN_URL)

    soup = BeautifulSoup(response.text, 'html.parser')

    content_p = soup.find_all('p')
    content_p = content_p[7]
    html_string = str(content_p)
    card_list = re.findall(r'(\d+/\d+).*"(.*?)".*"(.*?)"', html_string)
    print(card_list[0])
    for card in card_list:
        card_number = card[0]
        ability_list = '''01/260 
        10/260 
        29/260 
        45/260 
        54/260 
        56/260 
        58/260 
        60/260 
        62/260 
        66/260 
        102/260
        103/260
        120/260
        135/260
        159/260
        168/260
        169/260
        205/260
        220/260
        226/260
        228/260
        233/260
        236/260
        239/260
        248/260
        250/260
        253/260
        258/260'''
        abilities = [line.strip() for line in ability_list.strip().split('\n')]
        if card_number in abilities:
            name = card[2]
            try:
                response = scraper.get(BASE_URL + card[1])
                # print(BASE_URL + card[1])
                soup = BeautifulSoup(response.text, 'html.parser')
                content_p = soup.find_all('p')
                html_string = str(content_p)
                print(html_string + "\n\n")
                # if "Strength" not in html_string:
                #     print(f'{card_number} {name} not found!')

                # description_list = re.findall(
                #     r'Strength.*?(\d+).*[\r\n].*Agility.*?(\d+).*[\r\n].*Fighting.*?(\d+).*[\r\n].*Brains.*?(\d+)',
                #     html_string)
                # strength = int(description_list[0][0])
                # agility = int(description_list[0][1])
                # fighting = int(description_list[0][2])
                # brains = int(description_list[0][3])
                content_img = soup.find('img', class_='mw-file-element')
                img = get_high_res_img(content_img['src'])
                print(img)
                img_data = requests.get(img).content
                image_url = f'img/cards_abilities_1/{name}.png'
                with open(image_url, 'wb') as handler:
                    handler.write(img_data)
                cin = input()
                cin = cin.split(' ')
                if cin[0] == 'b':
                    cin[0] = 'buff'
                elif cin[0] == 'd':
                    cin[0] = 'debuff'
                elif cin[0] == 'b':
                    cin[0] = 'block'

                if cin[2] == 'a':
                    cin[2] = 'agility'
                elif cin[2] == 's':
                    cin[2] = 'strength'
                elif cin[2] == 'b':
                    cin[2] = 'brains'
                elif cin[2] == 'f':
                    cin[2] = 'fighting'

                print(cin)

                cur.execute('''
                INSERT INTO cards_abilities_1 (card_number, name, effect_type, effect_value, target, image_url) VALUES (?, ?, ?, ?, ?, ?)
                ''', (card_number, name, cin[0], cin[1], cin[2], 'default'))

                # cur.execute('''
                #             INSERT INTO cards (card_number, name, strength, agility, fighting, brains, image_url)
                #             VALUES (?, ?, ?, ?, ?, ?, ?)
                #             ''', (
                #                 card_number,
                #                 name,
                #                 strength,
                #                 agility,
                #                 fighting,
                #                 brains,
                #                 image_url
                #             ))
                conn.commit()
                time.sleep(0.5)
            except Exception as e:
                print(f"{e}, while processing {card_number}")

scrape_cards()
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
        name = card[2]
        try:
            response = scraper.get(BASE_URL + card[1])
            # print(BASE_URL + card[1])
            soup = BeautifulSoup(response.text, 'html.parser')
            content_p = soup.find_all('p')
            html_string = str(content_p)
            # print(html_string + "\n\n")
            if "Strength" not in html_string:
                print(f'{card_number} {name} not found!')
                time.sleep(1)
                continue
            description_list = re.findall(
                r'Strength.*?(\d+).*[\r\n].*Agility.*?(\d+).*[\r\n].*Fighting.*?(\d+).*[\r\n].*Brains.*?(\d+)',
                html_string)
            strength = int(description_list[0][0])
            agility = int(description_list[0][1])
            fighting = int(description_list[0][2])
            brains = int(description_list[0][3])
            content_img = soup.find('img', class_='mw-file-element')
            img = get_high_res_img(content_img['src'])
            # print(img)
            img_data = requests.get(img).content
            if not path.isfile(f'img/{name}.png'):
                print(f'{card_number} {name} not found!')
            # image_url = f'img/{name}.png'
            # with open(image_url, 'wb') as handler:
            #     handler.write(img_data)
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
            # conn.commit()
            time.sleep(0.5)
        except Exception as e:
            print(f"{e}, while processing {card_number}")


scrape_cards()

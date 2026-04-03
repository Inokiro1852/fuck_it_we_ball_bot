import re
import sqlite3
import requests

# imgURL = "https://static.wikia.nocookie.net/tmnt/images/b/b0/Set1-4-260-WayNinja-Tcard.png/revision/latest?cb=20230201183924"
#
# img_data = requests.get(imgURL).content
# with open('img/image_name.png', 'wb') as handler:
#     handler.write(img_data)

conn = sqlite3.connect('tmnt.db')
cur = conn.cursor()
photo_id = 'AgACAgIAAxkBAAIEL2nPhfcNqsAcQyeVS_oWGPNDPpPOAAJRFWsbaNR5SqGceRYAAZWdTwEAAwIAA3kAAzoE'
cur.execute('''
            INSERT INTO cards (card_number, name, strength, agility, fighting, brains, image_url) VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', ('0/260', 'Wrap', '0', '0', '0', '0', photo_id))
conn.commit()


# def get_high_res_img(img_url):
#     clean_url = re.sub(r'/revision.*', '', img_url)
#     return clean_url
#
# get_high_res_img('')


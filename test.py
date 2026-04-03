import re
import sqlite3
import requests

# imgURL = "https://static.wikia.nocookie.net/tmnt/images/b/b0/Set1-4-260-WayNinja-Tcard.png/revision/latest?cb=20230201183924"
#
# img_data = requests.get(imgURL).content
# with open('img/image_name.png', 'wb') as handler:
#     handler.write(img_data)


photo_id = 'AgACAgIAAxkBAAIEL2nPhfcNqsAcQyeVS_oWGPNDPpPOAAJRFWsbaNR5SqGceRYAAZWdTwEAAwIAA3kAAzoE'
conn = sqlite3.connect('tmnt.db')
cur = conn.cursor()
cur.execute('''
            SELECT strength, agility, fighting, brains
            FROM cards;
            ''')
row = cur.fetchall()
print(len(row))
zero_wins = one_wins = two_wins = three_wins = four_wins = 0

# Проходимося по кожній картці (це наша "атакуюча" картка)
for x in range(len(row)):

    # Проходимося по кожній картці знову (це наша "картка-захисник")
    for y in range(len(row)):

        # Картка не повинна битися сама з собою!
        if x == y:
            continue  # Пропускаємо цей крок і йдемо далі

        wins = 0

        # Порівнюємо статі: x (атакуючий) проти y (захисника)
        if row[x][0] > row[y][0]:
            wins += 1
        if row[x][1] > row[y][1]:
            wins += 1
        if row[x][2] > row[y][2]:
            wins += 1
        if row[x][3] > row[y][3]:
            wins += 1

        # Записуємо результат бою для картки x
        if wins == 0:
            zero_wins += 1
        elif wins == 1:
            one_wins += 1
        elif wins == 2:
            two_wins += 1
        elif wins == 3:
            three_wins += 1
        elif wins == 4:
            four_wins += 1

print(f"0 перемог: {zero_wins}")
print(f"1 перемога: {one_wins}")
print(f"2 перемоги: {two_wins}")
print(f"3 перемоги: {three_wins}")
print(f"4 перемоги: {four_wins}")

# conn.commit()


# def get_high_res_img(img_url):
#     clean_url = re.sub(r'/revision.*', '', img_url)
#     return clean_url
#
# get_high_res_img('')

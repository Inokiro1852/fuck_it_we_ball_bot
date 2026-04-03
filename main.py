import asyncio
import logging
import os
import random
import sys
import uuid
import aiosqlite
import html

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, \
    LinkPreviewOptions, ChosenInlineResult, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, \
    CallbackQuery
from dotenv import load_dotenv

from content import major_arcana, faggots, faggots_images

load_dotenv(".env")
BOT_TOKEN = os.environ.get('BOT_TOKEN')

dp = Dispatcher()

async def random_arcana():
    chance = random.random()
    if chance < 0.5:
        return 1, random.choice(list(major_arcana))
    elif chance < 0.85:
        return 2, random.choice(list(faggots))
    else:
        return 3, random.choice(list(faggots_images))


# @dp.message(Command('script'))
# async def print_msg_id(message: Message) -> None:
#     await message.answer("Starting sending photos...")
#     list_img = os.listdir('img')
#     async with aiosqlite.connect('tmnt.db') as db:
#         for img in list_img:
#             photo = FSInputFile(f'img/{img}')
#             sent_msg = await message.answer_photo(photo)
#             photo_id = sent_msg.photo[-1].file_id
#             print(photo_id)
#             await db.execute(
#                 "UPDATE cards SET image_url = ? WHERE image_url = ?",
#                 (photo_id, f'img/{img}')
#             )
#             await db.commit()
#
#             await asyncio.sleep(random.randint(1, 3))


# @dp.message()
# async def send_msg(message: Message) -> None:
#     await message.answer(str(message.photo))


@dp.message(CommandStart())
async def hello(message: Message) -> None:
    await message.answer(f"Fuck you, {message.from_user.first_name}!")


@dp.inline_query()
async def handle_all_inline_query(inline_query: InlineQuery) -> None:
    query = inline_query.query.strip()
    results = []

    # 1. prediction
    if not query.startswith("d"):
        prediction = await random_arcana()

        if prediction[0] == 1:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{major_arcana[prediction[1]]}",
                    )
                ))
        elif prediction[0] == 2:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{faggots[prediction[1]]}",
                    )
                ))
        else:
            photo_file_id = faggots_images[prediction[1]][1]
            caption_text = faggots_images[prediction[1]][0]
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=caption_text,
                        link_preview_options=LinkPreviewOptions(
                            url=photo_file_id,
                            show_above_text=False,
                            is_disabled=False
                        )
                    )
                ))

    # 2. dice roll (custom)
    if query.startswith("d") and len(query) > 1:
        try:
            number = int(query[1:])
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your dice 🎲",
                    description=f"(d{number})",
                    input_message_content=InputTextMessageContent(
                        message_text=f"<code>(d{number})</code>: {random.randint(1, number)}",
                    )
                ))
        except ValueError:
            pass

    # 3. dice roll static
    if not query.startswith("d"):
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Get your dice 🎲",
                description="(d20)",
                input_message_content=InputTextMessageContent(
                    message_text=f"<code>(d20)</code>: {random.randint(1, 20)}",
                )
            ))

        result_id = "tmnt_card"
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"Get your TMNT Card 🐢",
                description=f"A ninja never admits defeat...",
                input_message_content=InputTextMessageContent(
                    message_text=f"<i>Flipping the TMNT card...</i>",
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⏳ Flipping...", callback_data="loading")]
                ])
            )
        )
        result_id = "tmnt_fight"
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title=f"Duel using your TMNT Card 🥷",
                description=f"A ninja SOMETIMES admits defeat...",
                input_message_content=InputTextMessageContent(
                    message_text=f"<i>Preparing the battlefield...</i>",
                ),
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="🩸 Bleeding...", callback_data="bleeding")]
                ])
            )
        )
    await inline_query.answer(
        results=results,
        cache_time=0,
        is_personal=True,
    )


@dp.chosen_inline_result()
async def inline_result(chosen_result: ChosenInlineResult, bot: Bot):
    if not chosen_result.inline_message_id:
        return
    if chosen_result.result_id.startswith("tmnt_card"):
        async with aiosqlite.connect('tmnt.db') as db:
            async with db.execute(
                    'SELECT card_number, name, strength, agility, fighting, brains, image_url FROM cards ORDER BY RANDOM() LIMIT 1',
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    card_number, name, strength, agility, fighting, brains, image_url = row
                    caption_text = (f'<code>{card_number}</code>: <b>{name}</b>\n\n'
                                    f'<i>Strength: {strength}\n'
                                    f'Agility: {agility}\n'
                                    f'Fighting: {fighting}\n'
                                    f'Brains: {brains}</i>')
                    media = InputMediaPhoto(
                        media=image_url,
                        caption=caption_text,
                        parse_mode=ParseMode.HTML
                    )
                    await bot.edit_message_media(
                        inline_message_id=chosen_result.inline_message_id,
                        media=media
                    )
    elif chosen_result.result_id.startswith("tmnt_fight"):
        async with aiosqlite.connect('tmnt.db') as db:
            async with db.execute('SELECT image_url FROM cards WHERE card_number = "0/260"') as cursor:
                row = await cursor.fetchone()
                image_url = row[0]
                caption_text = (f'<code>0/260</code>: <b>Wrap</b>\n\n'
                                f'<i>Дуэлянт 1</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n'
                                f'<i>Дуэлянт 2</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n'
                                f'Ожидание дуэлянтов (0/2)...')
                media = InputMediaPhoto(
                    media=image_url,
                    caption=caption_text,
                    parse_mode=ParseMode.HTML
                )
                await bot.edit_message_media(
                    inline_message_id=chosen_result.inline_message_id,
                    media=media,
                    reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                        [InlineKeyboardButton(text='Вступить (0/2) ⚖️', callback_data='dueling')]
                    ])
                )


duels = {}


@dp.callback_query(F.data == 'dueling')
async def process_duel(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    if not inline_id:
        return
    user_id = callback_query.from_user.id
    user_name = html.escape(callback_query.from_user.first_name)
    if callback_query.from_user.last_name:
        user_name = html.escape(callback_query.from_user.first_name + ' ' + callback_query.from_user.last_name)

    if inline_id not in duels:
        duels[inline_id] = []

    players = duels[inline_id]

    players.append({'id': user_id, 'name': user_name})
    print(players)

    if len(players) == 1:
        await callback_query.answer('Ждём оппонента...')
        async with aiosqlite.connect('tmnt.db') as db:
            async with db.execute('SELECT image_url FROM cards WHERE card_number = "0/260"') as cursor:
                row = await cursor.fetchone()
                image_url = row[0]

        caption_text = f'<code>0/260</code>: <b>Wrap</b>\n\nДуэлянт 1: {user_name}\nДуэлянт 2: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\nОжидание дуэлянтов (1/2)...'
        media = InputMediaPhoto(media=image_url, caption=caption_text, parse_mode=ParseMode.HTML)

        await bot.edit_message_media(
            inline_message_id=inline_id,
            media=media,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Вступить (1/2) ⚖️', callback_data='dueling')]
            ])
        )
    elif len(players) == 2:
        p1, p2 = players[0], players[1]
        async with aiosqlite.connect('tmnt.db') as db:
            async with db.execute(
                    'SELECT card_number, name, strength, agility, fighting, brains, image_url FROM cards ORDER BY RANDOM() LIMIT 2') as cursor:
                cards = await cursor.fetchall()
        card1 = {"card_number": cards[0][0], "name": cards[0][1], "strength": cards[0][2], "agility": cards[0][3],
                 "fighting": cards[0][4], "brains": cards[0][5], "image_url": cards[0][6]}
        card2 = {"card_number": cards[1][0], "name": cards[1][1], "strength": cards[1][2], "agility": cards[1][3],
                 "fighting": cards[1][4], "brains": cards[1][5], "image_url": cards[1][6]}
        win1 = 0
        stats_text = ''
        attributes = ['Strength', 'Agility', 'Fighting', 'Brains']

        for attribute in attributes:
            val1 = card1[attribute.lower()]
            val2 = card2[attribute.lower()]

            if val1 > val2:
                win1 += 1
                symbol = '&gt;'
            elif val1 < val2:
                symbol = '&lt;'
            else:
                symbol = '='

            stats_text += f'<i>{attribute}: {val1} {symbol} {val2}</i>\n'

        caption_text = (
            f"⚔️ {p1['name']} вытянул <code>{card1['card_number']}</code>: <b>{card1['name']}</b>\n"
            f"⚔️ {p2['name']} вытянул <code>{card2['card_number']}</code>: <b>{card2['name']}</b>\n\n"
            f"{stats_text}\n\n")

        if win1 > 2:
            win_card, win_p = card1, p1
        elif win1 < 2:
            win_card, win_p = card2, p2
        else:
            caption_text += '🎲 Ничья! Но побеждает по воле судьбы...\n'
            if random.random() < 0.5:
                win_card, win_p = card1, p1
            else:
                win_card, win_p = card2, p2

        caption_text += f'🩸 {win_p['name']} победил!'

        media = InputMediaPhoto(media=win_card['image_url'], caption=caption_text, parse_mode=ParseMode.HTML)

        await bot.edit_message_media(
            inline_message_id=inline_id,
            media=media,
        )
        del duels[inline_id]


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

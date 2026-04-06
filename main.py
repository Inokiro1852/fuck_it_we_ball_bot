import asyncio
import io
import logging
import os
import random
import sys
import uuid

import PIL.Image
import aiosqlite
import html

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, \
    LinkPreviewOptions, ChosenInlineResult, InputMediaPhoto, InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, \
    CallbackQuery, BufferedInputFile
from dotenv import load_dotenv
from PIL import Image, ImageFilter

from content import major_arcana, faggots, faggots_images

load_dotenv(".env")
BOT_TOKEN = os.environ.get('BOT_TOKEN')

dp = Dispatcher()


async def get_random_tarot():
    chance = random.random()
    if chance < 0.5:
        return 1, random.choice(list(major_arcana))
    elif chance < 0.85:
        return 2, random.choice(list(faggots))
    else:
        return 3, random.choice(list(faggots_images))


async def fetch_card(card_number: str, columns: list[str], db_name: str = 'cards'):
    if not columns:
        columns = ('image_url',)
    for column in columns:
        if not column.isidentifier():
            raise ValueError(f'Column "{column}" is not a valid identifier')

    columns_str = ", ".join(columns)
    async with aiosqlite.connect('tmnt.db') as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                f'SELECT {columns_str} FROM {db_name} WHERE card_number = ?', (card_number,)
        ) as cursor:
            return await cursor.fetchone()


async def fetch_random_card(amount: int = 1):
    async with aiosqlite.connect("tmnt.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
                'SELECT card_number, name, strength, agility, fighting, brains, image_url '
                'FROM cards ORDER BY RANDOM() LIMIT ?',
                (amount,)
        ) as cursor:
            return await cursor.fetchall()

script_dir = os.path.dirname(os.path.abspath(__file__))

async def get_local_img_path(card_number: str):
    card = await fetch_card(card_number, ['name'])
    card_name = os.path.join(script_dir, 'img', f'{card["name"]}.png')
    return card_name


async def image_url_exists(card_number: str):
    card = await fetch_card(card_number, [], 'cards_glued')
    if card is None:
        return False
    return card['image_url']


def fix_aspect_ratio(img1: PIL.Image.Image, img2: PIL.Image.Image):
    aspect_ratio = img1.width / img1.height
    new_width = int(img2.height * aspect_ratio)
    img_wrap = img1.resize((new_width, img2.height))
    return img_wrap


def paste_and_save_img(img1: PIL.Image.Image, img2: PIL.Image.Image):
    dst = Image.new('RGB', (img1.width + img2.width, img1.height))
    dst.paste(img1, (0, 0))
    dst.paste(img2, (img1.width, 0))

    bio = io.BytesIO()
    dst.save(bio, 'PNG')
    return bio.getvalue()


def _sync_generate_state_1(img_path: str, wrap_path):
    img = Image.open(img_path)
    w, h = img.size
    box = (int(w * 0.85), int(h * 0.58), int(w * 0.98), int(h * 0.85))
    stats_area = img.crop(box)
    blurred_area = stats_area.filter(ImageFilter.GaussianBlur(radius=5))
    img.paste(blurred_area, box)

    img_wrap = Image.open(wrap_path)

    if img.height != img_wrap.height:
        img_wrap = fix_aspect_ratio(img_wrap, img)

    return paste_and_save_img(img, img_wrap)


def _sync_generate_state_2(img1_path: str, img2_path, winner: int):
    img1 = Image.open(img1_path)
    img2 = Image.open(img2_path)

    if winner == 1:
        img1 = img1.convert('L').convert('RGB')
    else:
        img2 = img2.convert('L').convert('RGB')

    if img1.height != img2.height:
        img2 = fix_aspect_ratio(img2, img1)

    return paste_and_save_img(img1, img2)


async def save_img_url(card_number_glued: str, image_url: str):
    async with aiosqlite.connect('tmnt.db') as db:
        await db.execute(
            "INSERT INTO cards_glued (card_number, image_url) VALUES (?, ?)",
            (card_number_glued, image_url)
        )
        await db.commit()


async def get_state_1_image(bot: Bot, card_number):
    img_exists_url = await image_url_exists(f'{card_number} 0/260')
    if img_exists_url:
        return img_exists_url
    else:
        img_path = await get_local_img_path(card_number)
        wrap_path = await get_local_img_path('0/260')
        img = await asyncio.to_thread(_sync_generate_state_1, img_path, wrap_path)
        msg = await bot.send_photo(
            chat_id=556610851,
            photo=BufferedInputFile(file=img, filename='glued.png')
        )
        image_url = msg.photo[-1].file_id
        await save_img_url(f'{card_number} 0/260', image_url)
        return image_url


async def get_state_2_image(bot: Bot, card_number1, card_number2, winner):
    img_exists_url = await image_url_exists(f'{card_number1} {card_number2}')
    if img_exists_url:
        return img_exists_url
    else:
        img1_path = await get_local_img_path(card_number1)
        img2_path = await get_local_img_path(card_number2)
        img = await asyncio.to_thread(_sync_generate_state_2, img1_path, img2_path, winner)
        msg = await bot.send_photo(
            chat_id=556610851,
            photo=BufferedInputFile(file=img, filename='glued.png')
        )
        image_url = msg.photo[-1].file_id
        await save_img_url(f'{card_number1} {card_number2}', image_url)
        return image_url


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

    # 1. dice roll (custom)
    if query.startswith("d") and query[1:].isdigit():
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
        await inline_query.answer(results=results, cache_time=0, is_personal=True)
        return

    # 2. prediction
    prediction_type, card = await get_random_tarot()

    if prediction_type == 1:
        text, link_preview_options = major_arcana[card], None
        link_preview_options = None
    elif prediction_type == 2:
        text, link_preview_options = faggots[card], None
        link_preview_options = None
    else:
        text = faggots_images[card][0]
        link_preview_options = LinkPreviewOptions(
            url=faggots_images[card][1],
            show_above_text=False,
            is_disabled=False
        )

    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Get your prediction 🎭",
            description="Good luck!",
            input_message_content=InputTextMessageContent(
                message_text=text,
                link_preview_options=link_preview_options
            )
        ))

    # 3. dice roll static
    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Get your dice 🎲",
            description="(d20)",
            input_message_content=InputTextMessageContent(
                message_text=f"<code>(d20)</code>: {random.randint(1, 20)}",
            )
        ))

    # 4. tmnt card
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

    # 5. tmnt dueling
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

    # handle tmnt card
    if chosen_result.result_id.startswith("tmnt_card"):
        card = await fetch_random_card()
        card_number, name, strength, agility, fighting, brains, image_url = card[0]
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

    # handle tmnt dueling
    elif chosen_result.result_id.startswith("tmnt_fight"):
        image = await fetch_card('0/260 0/260', [], 'cards_glued')
        image_url = image['image_url']
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
        user_name += html.escape(f' {callback_query.from_user.last_name}')

    if inline_id not in duels:
        duels[inline_id] = []

    players = duels[inline_id]

    cards = await fetch_random_card()
    players.append(
        {'id': user_id, 'name': user_name, 'card_number': cards[0]["card_number"]})
    print(players)

    if len(players) == 1:
        await callback_query.answer('Ждём оппонента...')
        image_url = await get_state_1_image(bot, players[0]['card_number'])

        caption_text = (f'<code>0/260</code>: <b>Wrap</b>\n\n'
                        f'Дуэлянт 1: {user_name}\n'
                        f'Дуэлянт 2: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n'
                        f'Ожидание дуэлянтов (1/2)...')
        media = InputMediaPhoto(media=image_url, caption=caption_text, parse_mode=ParseMode.HTML)

        await bot.edit_message_media(
            inline_message_id=inline_id,
            media=media,
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text='Вступить (1/2) ⚖️', callback_data='dueling')]
            ])
        )
    else:
        cards = (await fetch_card(players[0]['card_number'],
                                  ['name', 'card_number', 'strength', 'agility', 'fighting', 'brains']),
                 await fetch_card(players[1]['card_number'],
                                  ['name', 'card_number', 'strength', 'agility', 'fighting', 'brains']))
        win1 = 0
        stats_text = ''
        attributes = ['Strength', 'Agility', 'Fighting', 'Brains']

        for attribute in attributes:
            val1 = cards[0][attribute.lower()]
            val2 = cards[1][attribute.lower()]

            if val1 > val2:
                win1 += 1
                symbol = '&gt;'
            elif val1 < val2:
                symbol = '&lt;'
            else:
                symbol = '='

            stats_text += f'<i>{attribute}: {val1} {symbol} {val2}</i>\n'

        caption_text = (
            f"⚔️ {players[0]['name']} вытянул <code>{cards[0]['card_number']}</code>: <b>{cards[0]['name']}</b>\n"
            f"⚔️ {players[1]['name']} вытянул <code>{cards[1]['card_number']}</code>: <b>{cards[1]['name']}</b>\n\n"
            f"{stats_text}\n\n")

        if win1 > 2:
            winner, win_p = 0, players[0]
        elif win1 < 2:
            winner, win_p = 1, players[1]
        else:
            caption_text += '🎲 Ничья! Но побеждает по воле судьбы...\n'
            if random.random() < 0.5:
                winner, win_p = 0, players[0]
            else:
                winner, win_p = 1, players[1]

        caption_text += f'🩸 {win_p["name"]} победил!'

        image = await get_state_2_image(bot, cards[0]['card_number'], cards[1]['card_number'], winner)

        media = InputMediaPhoto(media=image, caption=caption_text, parse_mode=ParseMode.HTML)

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

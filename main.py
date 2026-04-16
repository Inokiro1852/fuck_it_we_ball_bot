import asyncio
import io
import logging
import os
import random
import sys
import uuid

import aiosqlite

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart, Command, Filter
from aiogram.utils.text_decorations import html_decoration
from aiogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    LinkPreviewOptions,
    ChosenInlineResult,
    InputMediaPhoto,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    FSInputFile,
    CallbackQuery,
    BufferedInputFile,
)
from dotenv import load_dotenv
from PIL import Image, ImageFilter

from content import major_arcana, faggots, faggots_images
from models import CharacterCard, AbilityCard, Player

load_dotenv('.env')
BOT_TOKEN = os.environ.get('BOT_TOKEN')
DUMP_CHAT_ID = int(os.environ.get('DUMP_CHAT_ID'))

dp = Dispatcher()

DB_CONN = None


async def on_startup():
    global DB_CONN
    DB_CONN = await aiosqlite.connect('tmnt.db')
    DB_CONN.row_factory = aiosqlite.Row


async def on_shutdown():
    await DB_CONN.close()


class IsAdmin(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.from_user.id == DUMP_CHAT_ID


async def get_random_tarot():
    chance = random.choices([1, 2, 3], weights=[0.5, 0.35, 0.15])[0]
    if chance == 1:
        return 1, random.choice(list(major_arcana))
    elif chance == 2:
        return 2, random.choice(list(faggots))
    else:
        return 3, random.choice(list(faggots_images))


async def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False,
):
    async with DB_CONN.execute(query, params) as cursor:
        if commit:
            await DB_CONN.commit()
        if fetch_one:
            return await cursor.fetchone()
        if fetch_all:
            return await cursor.fetchall()


async def fetch_card(card_number: str, columns: list[str], table_name: str = 'cards_1'):
    if not columns:
        columns = ('image_url',)
    for column in columns:
        if not column.isidentifier():
            raise ValueError(f'Column "{column}" is not a valid identifier')

    if not table_name.isidentifier():
        raise ValueError(f'Table name "{table_name}" is not a valid identifier')

    columns_str = ', '.join(columns)
    return await execute_query(
        query=f'SELECT {columns_str} FROM {table_name} WHERE card_number = ?',
        params=(card_number,),
        fetch_one=True,
    )


async def fetch_random_card(limit: int = 1):
    fetch_args = {'fetch_one': True} if limit == 1 else {'fetch_all': True}
    return await execute_query(
        query='SELECT card_number, name, strength, agility, fighting, brains, image_url FROM cards_1 ORDER BY RANDOM() LIMIT ?',
        params=(limit,),
        **fetch_args,
    )


async def fetch_random_ability_card(limit: int = 1):
    fetch_args = {'fetch_one': True} if limit == 1 else {'fetch_all': True}
    return await execute_query(
        query='SELECT card_number, name, effect_type, effect_value, target, image_url FROM cards_abilities_1 ORDER BY RANDOM() LIMIT ?',
        params=(limit,),
        **fetch_args,
    )


async def image_url_exists(card_number: str):
    card = await fetch_card(card_number, [], 'cards_glued_1')
    if card is None:
        return False
    return card['image_url']


async def save_img_url(card_number_glued: str, image_url: str):
    await execute_query(
        query='INSERT INTO cards_glued_1 (card_number, image_url) VALUES (?, ?)',
        params=(
            card_number_glued,
            image_url,
        ),
        commit=True,
    )


def _apply_filter(card):
    img = Image.open(card.path)

    if card.blur:
        box = (int(660 * 0.85), int(920 * 0.58), int(660 * 0.98), int(920 * 0.85))
        stats_area = img.crop(box)
        blurred_area = stats_area.filter(ImageFilter.GaussianBlur(radius=5))
        img.paste(blurred_area, box)

    if card.greyscale:
        img = img.convert('L').convert('RGB')

    return img


def _sync_glue_images(players: list[Player]):
    opened_imgs = []
    count_img = []
    for p in players:
        opened_imgs.append(_apply_filter(p.character))
        count = 1
        if p.ability:
            opened_imgs.append(_apply_filter(p.ability))
            count += 1
        count_img.append(count)

    img_width = opened_imgs[0].width
    img_height = opened_imgs[0].height
    print(players)
    print(len(opened_imgs))
    print(count_img)

    if count_img[0] == 2 or len(opened_imgs) > 2:
        # dst = Image.new('RGB', (img_width * 2, img_height * 2))
        dst = Image.open('img/Wrap4x4.png')
        if len(count_img) == 2:
            dst = dst.convert('L').convert('RGB')
        current_x = 0
        current_y = 0
        i = 0
        for count in count_img:
            while count != 0:
                dst.paste(opened_imgs[i], (current_x, current_y))
                current_x += img_width
                count -= 1
                i += 1
            current_x = 0
            current_y = img_height
    else:
        dst = Image.open('img/Wrap2x2.png')
        current_x = 0
        for img in opened_imgs:
            dst.paste(img, (current_x, 0))
            current_x += img.width

    bio = io.BytesIO()
    dst.save(bio, 'PNG')

    return bio.getvalue()


async def get_glued_images(bot: Bot, players: [Player]):
    img_numbers = []
    for p in players:
        img_numbers.append(p.character.number)
        if p.ability:
            img_numbers.append(p.ability.number)
    img_numbers = ' '.join(img_numbers)
    image_url_exists_str = await image_url_exists(img_numbers)
    if image_url_exists_str:
        return image_url_exists_str

    img = await asyncio.to_thread(_sync_glue_images, players)

    msg = await bot.send_photo(
        chat_id=DUMP_CHAT_ID, photo=BufferedInputFile(file=img, filename='glued.png')
    )
    image_url = msg.photo[-1].file_id
    await save_img_url(img_numbers, image_url)

    return image_url


@dp.message(Command('script'), IsAdmin())
async def print_msg_id(message: Message) -> None:
    await message.answer('Starting sending photos...')
    list_img = os.listdir('img/cards_1')
    for img in list_img:
        photo = FSInputFile(f'img/cards_1/{img}')
        name = img.split('.png')[0]
        sent_msg = await message.answer_photo(photo)
        photo_id = sent_msg.photo[-1].file_id
        print(photo_id)
        await execute_query(
            query='UPDATE cards_abilities_1 SET image_url = ? WHERE name = ?',
            params=(
                photo_id,
                name,
            ),
            commit=True,
        )

        await asyncio.sleep(0.1)


@dp.message(F.photo, IsAdmin())
async def send_photo_id(message: Message) -> None:
    await message.answer(str(message.photo))


@dp.message(CommandStart())
async def hello(message: Message) -> None:
    await message.answer(f'Fuck you, {message.from_user.first_name}!')


@dp.inline_query()
async def handle_all_inline_query(inline_query: InlineQuery) -> None:
    query = inline_query.query.strip()
    results = []

    # 1. dice roll (custom)
    if query.startswith('d') and query[1:].isdigit():
        number = int(query[1:])
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title='Get your dice 🎲',
                description=f'(d{number})',
                input_message_content=InputTextMessageContent(
                    message_text=f'<code>(d{number})</code>: {random.randint(1, number)}',
                ),
            )
        )
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
            url=faggots_images[card][1], show_above_text=False, is_disabled=False
        )

    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Get your prediction 🎭',
            description='Good luck!',
            input_message_content=InputTextMessageContent(
                message_text=text, link_preview_options=link_preview_options
            ),
        )
    )

    # 3. dice roll static
    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Get your dice 🎲',
            description='(d20)',
            input_message_content=InputTextMessageContent(
                message_text=f'<code>(d20)</code>: {random.randint(1, 20)}',
            ),
        )
    )

    # 4. tmnt card
    result_id = 'tmnt_card'
    results.append(
        InlineQueryResultArticle(
            id=result_id,
            title='Get your TMNT Card 🐢',
            description='A ninja never admits defeat...',
            input_message_content=InputTextMessageContent(
                message_text='<i>Flipping the TMNT card...</i>',
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='⏳ Flipping...', callback_data='loading'
                        )
                    ]
                ]
            ),
        )
    )

    # 5. tmnt dueling
    result_id = 'tmnt_fight'
    results.append(
        InlineQueryResultArticle(
            id=result_id,
            title='Duel using your TMNT Card 🥷',
            description='A ninja SOMETIMES admits defeat...',
            input_message_content=InputTextMessageContent(
                message_text='<i>Preparing the battlefield...</i>',
            ),
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='🩸 Bleeding...', callback_data='bleeding'
                        )
                    ]
                ]
            ),
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
    if chosen_result.result_id.startswith('tmnt_card'):
        card = await fetch_random_card()
        card_number, name, strength, agility, fighting, brains, image_url = card
        caption_text = (
            f'<code>{card_number}</code>: <b>{name}</b>\n\n'
            f'<i>Strength: {strength}\n'
            f'Agility: {agility}\n'
            f'Fighting: {fighting}\n'
            f'Brains: {brains}</i>'
        )
        media = InputMediaPhoto(
            media=image_url, caption=caption_text, parse_mode=ParseMode.HTML
        )
        await bot.edit_message_media(
            inline_message_id=chosen_result.inline_message_id, media=media
        )

    # handle tmnt dueling
    elif chosen_result.result_id.startswith('tmnt_fight'):
        image = await fetch_card('0/260 0/260', [], 'cards_glued_1')
        image_url = image['image_url']
        caption_text = (
            '<code>0/260</code>: <b>Wrap</b>\n\n'
            '<i>Дуэлянт 1</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n'
            '<i>Дуэлянт 2</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n'
            'Ожидание дуэлянтов (0/2)...'
        )
        media = InputMediaPhoto(
            media=image_url, caption=caption_text, parse_mode=ParseMode.HTML
        )
        await bot.edit_message_media(
            inline_message_id=chosen_result.inline_message_id,
            media=media,
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text='Вступить (0/2) ⚖️', callback_data='dueling'
                        )
                    ]
                ]
            ),
        )


duels = {}
locks = {}


async def calculate_duel_result(p1: Player, p2: Player):
    win1 = 0
    win2 = 0
    stats_text = ''
    attributes = ['strength', 'agility', 'fighting', 'brains']

    for p in [p1, p2]:
        if p.ability:
            if p.ability.target == 'any' or p.ability.effect_type == 'block':
                p.ability.target = random.choice(attributes)

    for attribute in attributes:
        p1_val = getattr(p1.character, attribute)
        p2_val = getattr(p2.character, attribute)

        def apply_ability(ability, val_1, val_2, attr):
            eff_1 = ''
            eff_2 = ''
            if not ability or ability.target not in ['all', attr]:
                return val_1, val_2, eff_1, eff_2

            effect_type = ability.effect_type
            effect_value = ability.effect_value

            if effect_type == 'block':
                val_2 = 0
                eff_2 = '[block]'
            elif effect_type == 'buff':
                val_1 += effect_value
                eff_1 = f'[+{effect_value}]'
            elif effect_type == 'debuff':
                val_2 -= effect_value
                eff_2 = f'[-{effect_value}]'

            return val_1, val_2, eff_1, eff_2

        p1_abil = p1.ability if p1.ability else None
        p2_abil = p2.ability if p2.ability else None

        eff_on_p1_str = ''
        eff_on_p2_str = ''

        p1_val, p2_val, eff_on_p1, eff_on_p2 = apply_ability(
            p1_abil, p1_val, p2_val, attribute
        )

        if eff_on_p1:
            eff_on_p1_str += f' {eff_on_p1}'
        if eff_on_p2:
            eff_on_p2_str += f' {eff_on_p2}'

        p2_val, p1_val, eff_on_p1, eff_on_p2 = apply_ability(
            p2_abil, p2_val, p1_val, attribute
        )

        if eff_on_p2:
            eff_on_p1_str += f' {eff_on_p2}'
        if eff_on_p1:
            eff_on_p2_str += f' {eff_on_p1}'

        if p1_val > p2_val:
            win1 += 1
            symbol = '&gt;'
        elif p1_val < p2_val:
            win2 += 1
            symbol = '&lt;'
        else:
            symbol = '='
        stats_text += f'<i>{attribute.capitalize()}: {p1_val}{eff_on_p1_str} {symbol} {p2_val}{eff_on_p2_str}</i>\n'

    ability_text_1 = ''
    if p1.ability:
        ability_text_1 = f'🎭 {p1.user_name} вытянул <code>{p1.ability.number}</code>: <b>{p1.ability.name}</b>\n'

    ability_text_2 = ''
    if p2.ability:
        ability_text_2 = f'🎭 {p2.user_name} вытянул <code>{p2.ability.number}</code>: <b>{p2.ability.name}</b>\n'

    caption_text = (
        f'⚔️ {p1.user_name} вытянул <code>{p1.character.number}</code>: <b>{p1.character.name}</b>\n'
        f'{ability_text_1}'
        f'⚔️ {p2.user_name} вытянул <code>{p2.character.number}</code>: <b>{p2.character.name}</b>\n'
        f'{ability_text_2}'
        f'\n{stats_text}\n'
    )

    if win1 > win2:
        win_p = p1
        if p2.ability:
            p2.ability.greyscale = True
        p2.character.greyscale = True
    elif win1 < win2:
        win_p = p2
        if p1.ability:
            p1.ability.greyscale = True
        p1.character.greyscale = True
    else:
        caption_text += '🎲 Ничья! Но побеждает по воле судьбы...\n'
        if random.random() < 0.5:
            win_p = p1
            if p2.ability:
                p2.ability.greyscale = True
            p2.character.greyscale = True
        else:
            win_p = p2
            if p1.ability:
                p1.ability.greyscale = True
            p1.character.greyscale = True

    caption_text += f'🩸 {win_p.user_name} победил!'

    return caption_text


async def delayed_cleanup(inline_id: str, delay: int = 3):
    await asyncio.sleep(delay)
    duels.pop(inline_id, None)
    locks.pop(inline_id, None)


@dp.callback_query(F.data == 'dueling')
async def process_duel(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    if not inline_id:
        return

    lock = locks.setdefault(inline_id, asyncio.Lock())

    async with lock:
        if duels.get(inline_id) == 'finished':
            await callback_query.answer('Битва шире окончена!')
            return
        if inline_id not in duels:
            duels[inline_id] = []
        players = duels[inline_id]
        user_id = callback_query.from_user.id
        user_name = html_decoration.quote(callback_query.from_user.first_name)
        if callback_query.from_user.last_name:
            user_name += html_decoration.quote(f' {callback_query.from_user.last_name}')

        if any(p.user_id == user_id for p in players):
            await callback_query.answer('Выйди и зайди нормально.')
            return

        if len(players) >= 2:
            await callback_query.answer('Дуэль заполнена!')
            return

        card = await fetch_random_card()
        character_card = CharacterCard.from_row(card)
        ability_card = None
        random_int = random.random()
        if random_int <= 0.5:
            ability = await fetch_random_ability_card()
            ability_card = AbilityCard.from_row(ability)

        new_player = Player(
            user_id=user_id,
            user_name=user_name,
            character=character_card,
            ability=ability_card if ability_card else None,
        )

        players.append(new_player)

        if len(players) == 1:
            await callback_query.answer('Ждём оппонента...')
            p1 = players[0]
            # print(p1)
            p1.character.blur = True
            image_url = await get_glued_images(bot, [p1])

            caption_text = (
                f'<code>0/260</code>: <b>Wrap</b>\n\n'
                f'Дуэлянт 1: {p1.user_name}\n'
                f'Дуэлянт 2: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n'
                f'Ожидание дуэлянтов (1/2)...'
            )
            media = InputMediaPhoto(
                media=image_url, caption=caption_text, parse_mode=ParseMode.HTML
            )

            await bot.edit_message_media(
                inline_message_id=inline_id,
                media=media,
                reply_markup=InlineKeyboardMarkup(
                    inline_keyboard=[
                        [
                            InlineKeyboardButton(
                                text='Вступить (1/2) ⚖️', callback_data='dueling'
                            )
                        ]
                    ]
                ),
            )
        elif len(players) == 2:
            await callback_query.answer('Битва начинается!')
            p1, p2 = players[0], players[1]
            # print(p1)
            p1.character.blur = False

            caption_text = await calculate_duel_result(p1, p2)

            image = await get_glued_images(bot, [p1, p2])

            media = InputMediaPhoto(
                media=image, caption=caption_text, parse_mode=ParseMode.HTML
            )

            await bot.edit_message_media(
                inline_message_id=inline_id,
                media=media,
            )
            duels[inline_id] = 'finished'
            asyncio.create_task(delayed_cleanup(inline_id))


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)
    await dp.start_polling(bot)


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

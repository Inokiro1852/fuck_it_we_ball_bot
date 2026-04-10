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

load_dotenv(".env")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

dp = Dispatcher()


async def get_random_tarot():
    chance = random.random()
    if chance < 0.5:
        return 1, random.choice(list(major_arcana))
    elif chance < 0.85:
        return 2, random.choice(list(faggots))
    else:
        return 3, random.choice(list(faggots_images))


async def fetch_card(card_number: str, columns: list[str], table_name: str = "cards_1"):
    if not columns:
        columns = ("image_url",)
    for column in columns:
        if not column.isidentifier():
            raise ValueError(f'Column "{column}" is not a valid identifier')

    columns_str = ", ".join(columns)
    async with aiosqlite.connect("tmnt.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            f"SELECT {columns_str} FROM {table_name} WHERE card_number = ?",
            (card_number,),
        ) as cursor:
            return await cursor.fetchone()


async def fetch_random_card(limit: int = 1):
    async with aiosqlite.connect("tmnt.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT card_number, name, strength, agility, fighting, brains, image_url "
            "FROM cards_1 ORDER BY RANDOM() LIMIT ?",
            (limit,),
        ) as cursor:
            if limit == 1:
                return await cursor.fetchone()
            else:
                return await cursor.fetchall()


async def fetch_random_ability_card():
    async with aiosqlite.connect("tmnt.db") as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            "SELECT card_number, name, effect_type, effect_value, target, image_url "
            "FROM cards_abilities_1 ORDER BY RANDOM() LIMIT 1",
        ) as cursor:
            return await cursor.fetchone()


script_dir = os.path.dirname(os.path.abspath(__file__))


async def get_local_img_path(card_number: str, table: str = "cards_1"):
    card = await fetch_card(card_number, ["name"], table)
    card_name = os.path.join(script_dir, f"img/{table}", f'{card["name"]}.png')
    return card_name


async def image_url_exists(card_number: str):
    card = await fetch_card(card_number, [], "cards_glued_1")
    if card is None:
        return False
    return card["image_url"]


async def save_img_url(card_number_glued: str, image_url: str):
    async with aiosqlite.connect("tmnt.db") as db:
        await db.execute(
            "INSERT INTO cards_glued_1 (card_number, image_url) VALUES (?, ?)",
            (card_number_glued, image_url),
        )
        await db.commit()


def _sync_glue_images(imgs: list[dict]):
    opened_imgs = []
    target_height = None
    for data in imgs:
        img = Image.open(data["path"])

        if data.get("blur"):
            w, h = img.size
            box = (int(w * 0.85), int(h * 0.58), int(w * 0.98), int(h * 0.85))
            stats_area = img.crop(box)
            blurred_area = stats_area.filter(ImageFilter.GaussianBlur(radius=5))
            img.paste(blurred_area, box)

        if data.get("greyscale"):
            img = img.convert("L").convert("RGB")

        if not target_height:
            target_height = img.height
        elif target_height != img.height:
            aspect_ratio = img.width / img.height
            new_width = int(aspect_ratio * target_height)
            img = img.resize((new_width, target_height))

        opened_imgs.append(img)

    total_width = sum(img.width for img in opened_imgs)

    dst = Image.new("RGB", (total_width, target_height))
    current_x = 0
    for img in opened_imgs:
        dst.paste(img, (current_x, 0))
        current_x += img.width

    bio = io.BytesIO()
    dst.save(bio, "PNG")

    return bio.getvalue()


async def get_glued_images(bot: Bot, img_list: list[dict]):
    img_numbers = ""
    for img in img_list:
        img_numbers += f'{img["card"]["card_number"]} '
        img["path"] = await get_local_img_path(img["card"]["card_number"], img["table"])
    img_numbers = img_numbers[:-1]
    image_url_exists_str = await image_url_exists(img_numbers)
    if image_url_exists_str:
        return image_url_exists_str

    img = await asyncio.to_thread(_sync_glue_images, img_list)

    msg = await bot.send_photo(
        chat_id=556610851, photo=BufferedInputFile(file=img, filename="glued.png")
    )
    image_url = msg.photo[-1].file_id
    await save_img_url(img_numbers, image_url)

    return image_url


@dp.message(Command("script"))
async def print_msg_id(message: Message) -> None:
    await message.answer("Starting sending photos...")
    list_img = os.listdir("img/cards_abilities_1")
    async with aiosqlite.connect("tmnt.db") as db:
        for img in list_img:
            photo = FSInputFile(f"img/cards_abilities_1/{img}")
            name = img.split(".png")[0]
            sent_msg = await message.answer_photo(photo)
            photo_id = sent_msg.photo[-1].file_id
            print(photo_id)
            await db.execute(
                "UPDATE cards_abilities_1 SET image_url = ? WHERE name = ?",
                (photo_id, name),
            )
            await db.commit()

            await asyncio.sleep(0.1)


@dp.message()
async def send_msg(message: Message) -> None:
    await message.answer(str(message.photo))


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
            title="Get your prediction 🎭",
            description="Good luck!",
            input_message_content=InputTextMessageContent(
                message_text=text, link_preview_options=link_preview_options
            ),
        )
    )

    # 3. dice roll static
    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title="Get your dice 🎲",
            description="(d20)",
            input_message_content=InputTextMessageContent(
                message_text=f"<code>(d20)</code>: {random.randint(1, 20)}",
            ),
        )
    )

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
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="⏳ Flipping...", callback_data="loading"
                        )
                    ]
                ]
            ),
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
            reply_markup=InlineKeyboardMarkup(
                inline_keyboard=[
                    [
                        InlineKeyboardButton(
                            text="🩸 Bleeding...", callback_data="bleeding"
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
    if chosen_result.result_id.startswith("tmnt_card"):
        card = await fetch_random_card()
        card_number, name, strength, agility, fighting, brains, image_url = card
        caption_text = (
            f"<code>{card_number}</code>: <b>{name}</b>\n\n"
            f"<i>Strength: {strength}\n"
            f"Agility: {agility}\n"
            f"Fighting: {fighting}\n"
            f"Brains: {brains}</i>"
        )
        media = InputMediaPhoto(
            media=image_url, caption=caption_text, parse_mode=ParseMode.HTML
        )
        await bot.edit_message_media(
            inline_message_id=chosen_result.inline_message_id, media=media
        )

    # handle tmnt dueling
    elif chosen_result.result_id.startswith("tmnt_fight"):
        image = await fetch_card("0/260 0/260", [], "cards_glued_1")
        image_url = image["image_url"]
        caption_text = (
            f"<code>0/260</code>: <b>Wrap</b>\n\n"
            f"<i>Дуэлянт 1</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n"
            f"<i>Дуэлянт 2</i>: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n"
            f"Ожидание дуэлянтов (0/2)..."
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
                            text="Вступить (0/2) ⚖️", callback_data="dueling"
                        )
                    ]
                ]
            ),
        )


duels = {}
locks = {}


@dp.callback_query(F.data == "dueling")
async def process_duel(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    if not inline_id:
        return
    if inline_id not in locks:
        locks[inline_id] = asyncio.Lock()

    async with locks[inline_id]:
        if duels.get(inline_id) == "finished":
            await callback_query.answer("Битва шире окончена!")
            return
        if inline_id not in duels:
            duels[inline_id] = []
        players = duels[inline_id]
        user_id = callback_query.from_user.id
        user_name = html.escape(callback_query.from_user.first_name)
        if callback_query.from_user.last_name:
            user_name += html.escape(f" {callback_query.from_user.last_name}")

        if any(p["id"] == user_id for p in players):
            await callback_query.answer("Выйди и зайди нормально.")
            return

        if len(players) >= 2:
            await callback_query.answer("Дуэль заполнена!")
            return

        card = await fetch_random_card()
        random_int = random.random()
        if random_int <= 0.5:
            ability = await fetch_random_ability_card()
        else:
            ability = False

        new_player = {
            "id": user_id,
            "user_name": user_name,
            "cards": [{"card": card, "table": "cards_1"}],
        }

        if ability:
            new_player["cards"].append({"card": ability, "table": "cards_abilities_1"})

        players.append(new_player)

        if len(players) == 1:
            await callback_query.answer("Ждём оппонента...")
            p1 = players[0]
            p1["cards"][0]["blur"] = True
            wrap_card = await fetch_card("0/260", ["card_number"])
            wrap = {"card": wrap_card, "table": "cards_1"}
            p1["cards"].append(wrap)
            image_url = await get_glued_images(bot, p1["cards"])

            caption_text = (
                f"<code>0/260</code>: <b>Wrap</b>\n\n"
                f"Дуэлянт 1: {p1['user_name']}\n"
                f"Дуэлянт 2: <tg-spoiler>ㅤㅤㅤㅤ</tg-spoiler>\n\n"
                f"Ожидание дуэлянтов (1/2)..."
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
                                text="Вступить (1/2) ⚖️", callback_data="dueling"
                            )
                        ]
                    ]
                ),
            )
        elif len(players) == 2:
            await callback_query.answer("Битва начинается!")
            p1, p2 = players[0], players[1]
            p1["cards"].pop()
            print(p1)
            del p1["cards"][0]["blur"]
            win1 = 0
            win2 = 0
            stats_text = ""
            attributes = ["Strength", "Agility", "Fighting", "Brains"]

            for p in [p1, p2]:
                if len(p["cards"]) == 2:
                    abil = p["cards"][1]["card"]
                    if abil["target"] == "any" or abil["effect_type"] == "block":
                        mutable_abil = dict(abil)
                        mutable_abil["target"] = random.choice(attributes).lower()
                        p["cards"][1]["card"] = mutable_abil

            for attribute in attributes:
                p1_val = p1["cards"][0]["card"][attribute.lower()]
                p2_val = p2["cards"][0]["card"][attribute.lower()]

                if len(p1["cards"]) == 2:
                    p1_abil = p1["cards"][1]["card"]
                    if p1_abil["effect_type"] == "block" and p1_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p2_val = 0
                    if p1_abil["effect_type"] == "buff" and p1_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p1_val += p1_abil["effect_value"]
                    if p1_abil["effect_type"] == "debuff" and p1_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p2_val -= p1_abil["effect_value"]
                if len(p2["cards"]) == 2:
                    p2_abil = p2["cards"][1]["card"]
                    if p2_abil["effect_type"] == "block" and p2_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p1_val = 0
                    if p2_abil["effect_type"] == "buff" and p2_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p2_val += p2_abil["effect_value"]
                    if p2_abil["effect_type"] == "debuff" and p2_abil["target"] in [
                        "all",
                        attribute.lower(),
                    ]:
                        p1_val -= p2_abil["effect_value"]

                if p1_val > p2_val:
                    win1 += 1
                    symbol = "&gt;"
                elif p1_val < p2_val:
                    win2 += 1
                    symbol = "&lt;"
                else:
                    symbol = "="
                stats_text += f"<i>{attribute}: {p1_val} {symbol} {p2_val}</i>\n"

            ability_text_1 = ""
            if len(p1["cards"]) == 2:
                ability_text_1 = f"🎭 {p1['user_name']} вытянул <code>{p1['cards'][1]['card']['card_number']}</code>: <b>{p1['cards'][1]['card']['name']}</b>\n"

            ability_text_2 = ""
            if len(p2["cards"]) == 2:
                ability_text_2 = f"🎭 {p2['user_name']} вытянул <code>{p2['cards'][1]['card']['card_number']}</code>: <b>{p2['cards'][1]['card']['name']}</b>\n"

            caption_text = (
                f"⚔️ {p1['user_name']} вытянул <code>{p1['cards'][0]['card']['card_number']}</code>: <b>{p1['cards'][0]['card']['name']}</b>\n"
                f"{ability_text_1}"
                f"⚔️ {p2['user_name']} вытянул <code>{p2['cards'][0]['card']['card_number']}</code>: <b>{p2['cards'][0]['card']['name']}</b>\n"
                f"{ability_text_2}"
                f"\n{stats_text}\n"
            )

            if win1 > win2:
                win_p = p1
                for card in p2["cards"]:
                    card["greyscale"] = True
            elif win1 < win2:
                win_p = p2
                for card in p1["cards"]:
                    card["greyscale"] = True
            else:
                caption_text += "🎲 Ничья! Но побеждает по воле судьбы...\n"
                if random.random() < 0.5:
                    win_p = p1
                    for card in p2["cards"]:
                        card["greyscale"] = True
                else:
                    win_p = p2
                    for card in p1["cards"]:
                        card["greyscale"] = True

            caption_text += f'🩸 {win_p["user_name"]} победил!'

            all_cards = p1["cards"] + (p2["cards"])

            image = await get_glued_images(bot, all_cards)

            media = InputMediaPhoto(
                media=image, caption=caption_text, parse_mode=ParseMode.HTML
            )

            await bot.edit_message_media(
                inline_message_id=inline_id,
                media=media,
            )
            duels[inline_id] = "finished"
    if inline_id not in duels and inline_id in locks:
        del locks[inline_id]


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

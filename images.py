import asyncio
import io

from aiogram import Bot
from aiogram.types import BufferedInputFile
from PIL import Image, ImageFilter

import db
from config import config
from models import Player


def _apply_filter(card):
    img = Image.open(card.path)
    x1 = int(660 * 0.85)
    y1 = int(920 * 0.58)
    x2 = int(660 * 0.98)
    y2 = int(920 * 0.85)

    if card.blur:
        box = ((x1), (y1), (x2), (y2))
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
    path_to_img_with_abilities = 'img/Wrap4x4.png'
    path_to_img_without_abilities = 'img/Wrap2x2.png'

    if count_img[0] == 2 or len(opened_imgs) > 2:
        # dst = Image.new('RGB', (img_width * 2, img_height * 2))
        dst = Image.open(path_to_img_with_abilities)
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
        dst = Image.open(path_to_img_without_abilities)
        current_x = 0
        for img in opened_imgs:
            dst.paste(img, (current_x, 0))
            current_x += img.width

    bio = io.BytesIO()
    dst.save(bio, 'PNG')

    for img in opened_imgs:
        img.close()
    dst.close()

    return bio.getvalue()


async def get_glued_images(bot: Bot, players: list[Player], table_name: str):
    img_numbers = []
    for p in players:
        img_numbers.append(p.character.get_attribute_and_number())
        if p.ability:
            img_numbers.append(p.ability.get_attribute_and_number())

    img_numbers = ' '.join(img_numbers)
    image_url_exists_str = await db.image_url_exists(img_numbers, table_name)
    if image_url_exists_str:
        return image_url_exists_str

    img = await asyncio.to_thread(_sync_glue_images, players)

    msg = await bot.send_photo(
        chat_id=config.dump_chat_id,
        photo=BufferedInputFile(file=img, filename='glued.png'),
    )
    image_url = msg.photo[-1].file_id
    await db.save_img_url(img_numbers, image_url, table_name)

    return image_url

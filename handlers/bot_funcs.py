import html
import random
import re
from io import BytesIO
from urllib.request import urlopen

import aiohttp
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.types import LinkPreviewOptions, Message
from aiogram.utils.media_group import MediaGroupBuilder
from PIL import Image

router = Router()


async def get_twitter_data(tweet: str):
    api_url = tweet.replace('https://x.com', 'https://api.fxtwitter.com')
    async with aiohttp.ClientSession() as session, session.get(api_url) as response:
        if response.status == 200:
            return await response.json()
        return None


async def get_tweet_caption(tweet, link):
    text = tweet.get('text', '')
    text = html.escape(text)
    author_name = tweet.get('author', {}).get('name')
    caption = (
        f'{author_name}:\n{text}\n\n<a href="{link}">link</a>'
        if text
        else f'{author_name}: <a href="{link}">link</a>'
    )
    return caption


def glue_images(link):
    Image.open(BytesIO(urlopen(link)).read())


async def send_tweet(tweet, message, caption, spoiler, glue):
    try:
        if isinstance(message, list):
            message = message[0]
        sent = None
        if tweet.get('media', {}).get('videos', []):
            video_info = tweet['media']['videos'][0]
            video_url = video_info['url']
            if video_info.get('type') == 'gif':
                sent = await message.reply_animation(
                    animation=video_url,
                    caption=caption,
                    has_spoiler=spoiler,
                    parse_mode=ParseMode.HTML,
                )
            else:
                sent = await message.reply_video(
                    video=video_url,
                    caption=caption,
                    has_spoiler=spoiler,
                    parse_mode=ParseMode.HTML,
                )
        elif tweet.get('media', {}).get('photos', []):
            # glue_images(tweet['media']['photos'][0])
            if glue and tweet.get('media', {}).get('mosaic', []):
                photo_url = tweet['media']['mosaic']['formats']['jpeg']
                sent = await message.reply_photo(
                    photo=photo_url,
                    caption=caption,
                    has_spoiler=spoiler,
                    parse_mode=ParseMode.HTML,
                )
            else:
                media_builder = MediaGroupBuilder(caption=caption)
                for photo in tweet['media']['photos']:
                    media_builder.add_photo(
                        media=photo['url'],
                        has_spoiler=spoiler,
                    )
                sent = await message.reply_media_group(
                    media=media_builder.build(),
                    parse_mode=ParseMode.HTML,
                )
        else:
            sent = await message.reply(
                text=caption,
                parse_mode=ParseMode.HTML,
                link_preview_options=LinkPreviewOptions(is_disabled=True),
            )
        return sent
    except Exception as e:
        print(e)
        await message.reply('No luck, fam ^^')


@router.message(F.text)
async def fixing_twitter_links(message: Message):
    message_text = message.text
    message_text = message_text.strip()
    pattern = r'(?<!\S)([dDдД](\d+))(?!\S)'
    search = re.search(pattern, message_text)
    if search and message.from_user.id != 8636035849 and not message.forward_from:
        print(search.groups())
        number = int(search.groups()[1])
        number = min(number, 9999)
        number = max(number, 2)
        message_text = f'<code>(d{number})</code>: {random.randint(1, number)}'
        await message.reply(message_text)
        return
    message_text = message_text.split()
    if 'https://x.com' in message_text[0]:
        response = await get_twitter_data(message_text[0])
        # print(response)
        tweet = response['tweet']
        spoiler = False
        glue = False
        reply = False
        for parameter in message_text[1:]:
            if parameter == 's' or parameter == 'с':
                spoiler = True
            if parameter == 'r' or parameter == 'р':
                reply = True
            if parameter == 'g' or parameter == 'к':
                glue = True
        caption = await get_tweet_caption(tweet, message_text[0])
        sent = await send_tweet(tweet, message, caption, spoiler, glue)
        if reply and tweet.get('quote', {}):
            tweet = tweet.get('quote', {})
            caption = await get_tweet_caption(tweet, message_text[0])
            await send_tweet(tweet, sent, caption, spoiler, glue)
        await message.delete()

import aiohttp
from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.media_group import MediaGroupBuilder

router = Router()


async def get_twitter_data(tweet: str):
    api_url = tweet.replace('https://x.com', 'https://api.fxtwitter.com')
    async with aiohttp.ClientSession() as session, session.get(api_url) as response:
        if response.status == 200:
            return await response.json()
        return None


async def get_tweet_caption(tweet):
    text = tweet.get('text', '')
    author_name = tweet.get('author', {}).get('name')
    caption = f'{author_name}:\n{text}' if text else None
    return caption


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
                    animation=video_url, caption=caption, has_spoiler=spoiler
                )
            else:
                sent = await message.reply_video(
                    video=video_url, caption=caption, has_spoiler=spoiler
                )
        elif tweet.get('media', {}).get('photos', []):
            if glue and tweet.get('media', {}).get('mosaic', []):
                photo_url = tweet['media']['mosaic']['formats']['jpeg']
                sent = await message.reply_photo(
                    photo=photo_url, caption=caption, has_spoiler=spoiler
                )
            else:
                media_builder = MediaGroupBuilder(caption=caption)
                for photo in tweet['media']['photos']:
                    media_builder.add_photo(media=photo['url'], has_spoiler=spoiler)
                sent = await message.reply_media_group(media=media_builder.build())
        else:
            sent = await message.reply(text=caption)
        return sent
    except Exception:
        message.reply('No luck, fam ^^')


@router.message(F.text)
async def fixing_twitter_links(message: Message):
    message_text = message.text
    message_text = message_text.strip()
    message_text = message_text.split()
    # chat_id = message.chat.id
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
        caption = await get_tweet_caption(tweet)
        sent = await send_tweet(tweet, message, caption, spoiler, glue)
        if reply and tweet.get('quote', {}):
            tweet = tweet.get('quote', {})
            caption = await get_tweet_caption(tweet)
            await send_tweet(tweet, sent, caption, spoiler, glue)

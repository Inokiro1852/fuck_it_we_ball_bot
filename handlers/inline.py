import random
import uuid

from aiogram import Bot, Router
from aiogram.enums import ParseMode
from aiogram.types import (
    ChosenInlineResult,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InlineQuery,
    InlineQueryResultArticle,
    InputMediaAnimation,
    InputMediaPhoto,
    InputMediaVideo,
    InputTextMessageContent,
    LinkPreviewOptions,
)

import db
import game.cards as game_cards
import handlers.bot_funcs as twitter
from content import faggots, faggots_images, major_arcana

router = Router()

DUMP_CHAT_ID = 556610851


@router.inline_query()
async def handle_all_inline_query(inline_query: InlineQuery) -> None:
    query = inline_query.query.strip()
    results = []
    reply_markup = None
    link_preview_options = None

    # 1. dice roll (custom)
    if query.startswith('d') and query[1:].isdigit():
        number = int(query[1:])
        number = min(number, 9999)
        message_text = f'<code>(d{number})</code>: {random.randint(1, number)}'
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title='Get your dice 🎲',
                description=f'(d{number})',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
            )
        )
        await inline_query.answer(results=results, cache_time=0, is_personal=True)
        return

    # 2. tmnt duel (custom)
    if query[0:].isdigit():
        result_id = '2'
        number = int(query[0:])
        if number < 2:
            number = 3
        elif number > 9:
            number = 9
        elif number % 2 == 0:
            number += 1
        result_id = f'tmnt_duel {number}'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text='Bleeding... 🩸', callback_data='bleeding')]
            ]
        )
        message_text = '<i>Preparing the battlefield...</i>'
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title='Duel using your TMNT Card 🥷',
                description='A ninja SOMETIMES admits defeat...',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
                reply_markup=reply_markup,
            )
        )
        await inline_query.answer(results=results, cache_time=0, is_personal=True)
        return

    # 3. prediction
    prediction_type, card = await game_cards.get_random_tarot()
    if prediction_type == 1:
        message_text = major_arcana[card]
        link_preview_options = None
    elif prediction_type == 2:
        message_text = faggots[card]
        link_preview_options = None
    else:
        message_text = faggots_images[card][0]
        link_preview_options = LinkPreviewOptions(
            url=faggots_images[card][1], show_above_text=False, is_disabled=False
        )

    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Get your prediction 🎭',
            description='Good luck!',
            input_message_content=InputTextMessageContent(
                message_text=message_text, link_preview_options=link_preview_options
            ),
        )
    )

    # 4. dice roll
    message_text = f'<code>(d20)</code>: {random.randint(1, 20)}'
    results.append(
        InlineQueryResultArticle(
            id=str(uuid.uuid4()),
            title='Get your dice 🎲',
            description='(d20)',
            input_message_content=InputTextMessageContent(
                message_text=message_text,
            ),
        )
    )

    # 5. tmnt card
    result_id = 'tmnt_card'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Flipping... ⏳', callback_data='loading')]
        ]
    )
    message_text = '<i>Flipping the TMNT card...</i>'
    results.append(
        InlineQueryResultArticle(
            id=result_id,
            title='Get your TMNT Card 🐢',
            description='A ninja never admits defeat...',
            input_message_content=InputTextMessageContent(
                message_text=message_text,
            ),
            reply_markup=reply_markup,
        )
    )

    # 6. tmnt dueling
    result_id = 'tmnt_duel'
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text='Bleeding... 🩸', callback_data='bleeding')]
        ]
    )
    message_text = '<i>Preparing the battlefield...</i>'
    results.append(
        InlineQueryResultArticle(
            id=result_id,
            title='Duel using your TMNT Card 🥷',
            description='A ninja SOMETIMES admits defeat...',
            input_message_content=InputTextMessageContent(
                message_text=message_text,
            ),
            reply_markup=reply_markup,
        )
    )

    # 7. twitter
    if 'https://x.com/' in query:
        results.clear()
        link = query.strip()
        link = link.split()
        link = link[0]
        message_text = '<i>Buying crack...</i>'
        result_id = 'none'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Fetching tweet...', callback_data='loading'
                    )
                ]
            ]
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title='Fetch tweet',
                description='Twin 💋',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
                reply_markup=reply_markup,
            )
        )
        result_id = 's'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Fetching tweet with spoiler...',
                        callback_data='loading',
                    )
                ]
            ]
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title='Fetch tweet with spoiler',
                description='I 😩',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
                reply_markup=reply_markup,
            )
        )

        result_id = 'r'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Fetching tweet with reply...',
                        callback_data='loading',
                    )
                ]
            ]
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title='Fetch tweet with reply',
                description='Love 😳',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
                reply_markup=reply_markup,
            )
        )

        result_id = 'sr'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text='Fetching tweet with spoiler and reply...',
                        callback_data='loading',
                    )
                ]
            ]
        )
        results.append(
            InlineQueryResultArticle(
                id=result_id,
                title='Fetch tweet with spoiler and reply',
                description='You 💘',
                input_message_content=InputTextMessageContent(
                    message_text=message_text,
                ),
                reply_markup=reply_markup,
            )
        )

    await inline_query.answer(
        results=results,
        cache_time=0,
        is_personal=True,
    )


async def send_tweet(bot, message_id, tweet, caption, spoiler, reply):
    if tweet.get('media', {}).get('videos', []):
        video_info = tweet['media']['videos'][0]
        if video_info.get('type') == 'gif':
            gif = InputMediaAnimation(
                media=video_info['url'], caption=caption, has_spoiler=spoiler
            )
            await bot.send_animation(DUMP_CHAT_ID, video_info['url'])
            await bot.edit_message_media(media=gif, inline_message_id=message_id)
        else:
            video = InputMediaVideo(
                media=video_info['url'], caption=caption, has_spoiler=spoiler
            )
            await bot.send_video(DUMP_CHAT_ID, video_info['url'])
            await bot.edit_message_media(media=video, inline_message_id=message_id)
    elif tweet.get('media', {}).get('photos', []):
        photo_url = tweet['media']['photos'][0]['url']
        photo = InputMediaPhoto(media=photo_url, caption=caption, has_spoiler=spoiler)
        await bot.send_photo(DUMP_CHAT_ID, photo_url)
        await bot.edit_message_media(media=photo, inline_message_id=message_id)
    else:
        await bot.edit_message_text(
            text=caption,
            inline_message_id=message_id,
            link_preview_options=LinkPreviewOptions(is_disabled=True),
        )


@router.chosen_inline_result()
async def inline_result(chosen_result: ChosenInlineResult, bot: Bot):
    if not chosen_result.inline_message_id:
        return

    # handle tmnt card
    if chosen_result.result_id.startswith('tmnt_card'):
        table_name, _, _ = await game_cards.get_random_card_set()
        card = await db.fetch_random_card(table_name)
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
            inline_message_id=chosen_result.inline_message_id,
            media=media,
        )

    # handle tmnt dueling
    elif chosen_result.result_id.startswith('tmnt_duel'):
        image = await db.fetch_card('0/260 0/260', [], 'cards_glued_1')
        image_url = image['image_url']
        chosen_results = chosen_result.result_id.split()
        caption_text = '<i>👾 Раунд 1 / 1</i>\n'
        callback_data = 'duel'
        if len(chosen_results) == 2:
            caption_text = f'<i>👾 Раунд 1 / {chosen_results[1]}</i>\n'
            callback_data = f'duel {chosen_results[1]}'

        caption_text += (
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
                            text='Вступить (0/2) ⚖️', callback_data=callback_data
                        )
                    ]
                ]
            ),
        )
    # twiter
    elif chosen_result.query.startswith('https://x.com/'):
        link = chosen_result.query.strip()
        data = chosen_result.result_id
        spoiler = False
        reply = False
        if data == 's':
            spoiler = True
        elif data == 'r':
            reply = True
        elif data == 'sr':
            spoiler = True
            reply = True
        response = await twitter.get_twitter_data(link)
        tweet = response['tweet']
        print(spoiler)
        caption = await twitter.get_tweet_caption(tweet, link)
        await send_tweet(
            bot, chosen_result.inline_message_id, tweet, caption, spoiler, reply
        )

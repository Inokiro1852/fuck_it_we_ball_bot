import random

from aiogram import Bot, F, Router
from aiogram.enums import ParseMode
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from aiogram.utils.text_decorations import html_decoration

import db
import game.cards as game_cards
import game.duel as game_duel
import images
import models
from duel_state import DuelManager

router = Router()
duel_state = DuelManager()


@router.callback_query(F.data.startswith('duel'))
async def process_duel(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    if not inline_id:
        return
    lock = await duel_state.get_lock(inline_id)
    async with lock:
        if await duel_state.is_finished(inline_id):
            await callback_query.answer('Битва шире окончена!')
            return
        tables = await game_cards.get_random_card_set()
        duel = await duel_state.create_duel(inline_id, tables)
        if duel is None:
            await callback_query.answer('Битва шире окончена!')
            return
        card_table, ability_table, glued_table = duel['tables']
        players = duel['players']
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

        card = await db.fetch_random_card(card_table)
        character_card = models.CharacterCard.from_row(card, card_table)
        ability_card = None
        random_int = random.random()
        if random_int <= 0.5:
            ability = await db.fetch_random_ability_card(ability_table)
            ability_card = models.AbilityCard.from_row(ability, ability_table)

        new_player = models.Player(
            user_id=user_id,
            user_name=user_name,
            character=character_card,
            ability=ability_card,
        )

        players.append(new_player)
        if len(players) == 1:
            await callback_query.answer('Ждём оппонента...')
            p1 = players[0]
            p1.character.blur = True
            image_url = await images.get_glued_images(bot, [p1], glued_table)
            caption_text = '<i>👾 Раунд 1 / 1</i>\n'
            data = callback_query.data.split()
            if len(data) == 2:
                caption_text = f'<i>👾 Раунд 1 / {data[1]}</i>\n'

            caption_text += (
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
                                text='Вступить (1/2) ⚖️',
                                callback_data=callback_query.data,
                            )
                        ]
                    ]
                ),
            )
            await duel_state.schedule_terminate_duel(inline_id)
        elif len(players) == 2:
            await callback_query.answer('Битва начинается!')
            p1, p2 = players[0], players[1]
            p1.character.blur = False
            data = callback_query.data.split()
            reply_markup = None
            if len(data) == 2:
                number = data[1]
                if number == '2':
                    text = 'Финальный раунд 🪬'
                else:
                    text = 'Раунд 2 🌀'
                callback_data = (
                    f'finish {number}' if number == '2' else f'round 2 {number}'
                )
                reply_markup = InlineKeyboardMarkup(
                    inline_keyboard=[
                        [InlineKeyboardButton(text=text, callback_data=callback_data)]
                    ]
                )
                caption_text = await game_duel.calculate_result(p1, p2, 1, number)
            else:
                caption_text = await game_duel.calculate_result(p1, p2, 1, 1)
                await duel_state.mark_finished(inline_id)
            image = await images.get_glued_images(bot, [p1, p2], glued_table)
            media = InputMediaPhoto(
                media=image,
                caption=caption_text,
                parse_mode=ParseMode.HTML,
            )

            await bot.edit_message_media(
                inline_message_id=inline_id,
                media=media,
                reply_markup=reply_markup,
            )


@router.callback_query(F.data.startswith('round'))
async def process_rounds(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    lock = await duel_state.get_lock(inline_id)
    async with lock:
        if await duel_state.is_finished(inline_id):
            await callback_query.answer('Битва шире окончена!')
            return
        await callback_query.answer()
        data = callback_query.data.split()

        if len(data) == 3:
            target_round = int(data[1])
            total_rounds = int(data[2])
        else:
            target_round = None
            total_rounds = int(data[1])
        duel = await duel_state.get_duel(inline_id)
        if not duel:
            await callback_query.answer('Время дуэли истекло!')
            return
        players = duel['players']
        card_table, ability_table, glued_table = duel['tables']
        if not any(p.user_id == callback_query.from_user.id for p in players):
            await callback_query.answer('Тебе суждено наблюдать.')
            return

        current_round = len(players) // 2

        if target_round is not None and current_round >= target_round:
            return

        if current_round + 1 >= total_rounds:
            return

        if current_round != total_rounds:
            await game_duel.prepare_players(players, card_table, ability_table)

        current_round += 1
        p1_index = (current_round - 1) * 2
        p2_index = p1_index + 1
        caption_text = await game_duel.calculate_result(
            players[p1_index], players[p2_index], current_round, total_rounds
        )
        image = await images.get_glued_images(
            bot, [players[p1_index], players[p2_index]], glued_table
        )
        text = ''
        callback_data = ''
        if current_round + 1 == total_rounds:
            text = 'Финальный раунд 🪬'
            callback_data = f'finish {total_rounds}'
        else:
            text = f'Раунд {current_round + 1} 🌀'
            callback_data = f'round {current_round + 1} {total_rounds}'
        reply_markup = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=text, callback_data=callback_data)]
            ]
        )

        media = InputMediaPhoto(
            media=image,
            caption=caption_text,
            parse_mode=ParseMode.HTML,
        )

        await bot.edit_message_media(
            inline_message_id=inline_id,
            media=media,
            reply_markup=reply_markup,
        )


@router.callback_query(F.data.startswith('finish'))
async def process_duels(callback_query: CallbackQuery, bot: Bot):
    inline_id = callback_query.inline_message_id
    data = callback_query.data.split()
    total_rounds = int(data[1])
    lock = await duel_state.get_lock(inline_id)
    async with lock:
        if await duel_state.is_finished(inline_id):
            await callback_query.answer('Битва шире окончена!')
            return
        duel = await duel_state.get_duel(inline_id)
        if not duel:
            await callback_query.answer('Время дуэли истекло!')
            return
        players = duel['players']
        card_table, ability_table, glued_table = duel['tables']
        if not any(p.user_id == callback_query.from_user.id for p in players):
            await callback_query.answer('Тебе суждено наблюдать.')
            return

        current_round = len(players) // 2

        if current_round >= total_rounds:
            return

        if current_round != total_rounds:
            await game_duel.prepare_players(players, card_table, ability_table)

        current_round += 1
        p1_index = (current_round - 1) * 2
        p2_index = p1_index + 1
        caption_text = await game_duel.calculate_result(
            players[p1_index], players[p2_index], current_round, total_rounds
        )
        caption_text += '\n\n🏆 Итоги турнира:\n'
        win1 = 0
        win2 = 0
        for i in range(0, len(players), 2):
            round = i // 2 + 1
            if players[i].character.greyscale:
                win2 += 1
                caption_text += (
                    f'{players[i + 1].user_name} победил в раунде <i>{round}</i>.\n'
                )
            else:
                win1 += 1
                caption_text += (
                    f'{players[i].user_name} победил в раунде <i>{round}</i>.\n'
                )
        if win1 > win2:
            caption_text += (
                f'\n🎊 {players[0].user_name} победил в <b>{win1}/{total_rounds}</b>!'
            )
        else:
            caption_text += (
                f'\n🎊 {players[1].user_name} победил в <b>{win2}/{total_rounds}</b>!'
            )

        image = await images.get_glued_images(
            bot, [players[p1_index], players[p2_index]], glued_table
        )

        reply_markup = None
        media = InputMediaPhoto(
            media=image,
            caption=caption_text,
            parse_mode=ParseMode.HTML,
        )

        await bot.edit_message_media(
            inline_message_id=inline_id,
            media=media,
            reply_markup=reply_markup,
        )

        await duel_state.mark_finished(inline_id)

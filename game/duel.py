import random

import db
import models


async def calculate_result(p1, p2, start: int, end: int):
    win1 = 0
    win2 = 0
    stats_text = ''
    attributes = ['strength', 'agility', 'fighting', 'brains']

    for p in [p1, p2]:
        if p.ability and p.ability.target == 'any':
            p.ability.target = random.choice(attributes)

    p1_sum = 0
    p2_sum = 0

    for attribute in attributes:
        p1_val = getattr(p1.character, attribute)
        p2_val = getattr(p2.character, attribute)

        def apply_ability(ability, val_1, val_2, attr):
            eff_1 = ''
            eff_2 = ''
            if not ability:
                return val_1, val_2, eff_1, eff_2

            targets = str(ability.target).split()
            effect_values = str(ability.effect_value).split()

            target_index = -1
            if 'all' in targets:
                target_index = 0
            elif attr in targets:
                target_index = targets.index(attr)
            else:
                return val_1, val_2, eff_1, eff_2

            effect_value = effect_values[target_index]
            effect_type = ability.effect_type

            if effect_type == 'block':
                val_2 = 0
                eff_2 = '[block]'
            elif effect_type == 'buff':
                if effect_value == 'x2':
                    val_1 *= 2
                    eff_1 = f'[{effect_value}]'
                else:
                    val_1 += int(effect_value)
                    eff_1 = f'[+{effect_value}]'
            elif effect_type == 'debuff':
                val_2 -= int(effect_value)
                val_2 = max(0, val_2)
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

        p1_sum += p1_val
        p2_sum += p2_val

    ability_text_1 = ''
    if p1.ability:
        ability_text_1 = f'🎭 {p1.user_name} вытянул <code>{p1.ability.number}</code>: <b>{p1.ability.name}</b>\n'

    ability_text_2 = ''
    if p2.ability:
        ability_text_2 = f'🎭 {p2.user_name} вытянул <code>{p2.ability.number}</code>: <b>{p2.ability.name}</b>\n'

    caption_text = (
        f'<i>👾 Раунд {start} / {end}</i>\n'
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
        if p1_sum <= 0 and p2_sum <= 0:
            p1_win_chance = 0.5
        else:
            exponent = 4
            p1_weight = p1_sum**exponent
            p2_weight = p2_sum**exponent
            p1_win_chance = p1_weight / (p1_weight + p2_weight)

        chance_text_1 = round(p1_win_chance * 100)
        chance_text_2 = 100 - chance_text_1
        caption_text += f'🎲 Ничья! Шансы на победу: {chance_text_1} / {chance_text_2}. Но по воле судьбы...\n'
        if random.random() < p1_win_chance:
            win_p = p1
            if p2.ability:
                p2.ability.greyscale = True
            p2.character.greyscale = True
        else:
            win_p = p2
            if p1.ability:
                p1.ability.greyscale = True
            p1.character.greyscale = True

    caption_text += f'{win_p.user_name} победил! 🩸'

    return caption_text


async def prepare_players(players, card_table, ability_table):
    for y in range(2):
        card = await db.fetch_random_card(card_table)
        character_card = models.CharacterCard.from_row(card, card_table)
        ability_card = None
        random_int = random.random()
        if random_int <= 0.5:
            ability = await db.fetch_random_ability_card(ability_table)
            ability_card = models.AbilityCard.from_row(ability, ability_table)

        new_player = models.Player(
            user_id=players[y].user_id,
            user_name=players[y].user_name,
            character=character_card,
            ability=ability_card,
        )
        players.append(new_player)

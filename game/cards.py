import random

import content


async def get_random_tarot():
    chance = random.choices([1, 2, 3], weights=[0.45, 0.45, 0.1])[0]
    if chance == 1:
        return 1, random.choice(list(content.major_arcana))
    elif chance == 2:
        return 2, random.choice(list(content.faggots))
    else:
        return 3, random.choice(list(content.faggots_images))


async def get_random_card_set(index: int | None = None):
    sets = [
        ['cards_1', 'cards_abilities_1', 'cards_glued_1'],
        ['cards_2', 'cards_abilities_2', 'cards_glued_2'],
        ['cards_3', 'cards_abilities_3', 'cards_glued_3'],
    ]
    if index:
        return sets[index]
    choice = random.choice(sets)
    return choice

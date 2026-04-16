from dataclasses import dataclass
from typing import Optional
from pathlib import Path


script_dir = Path(__file__).parent


@dataclass
class CharacterCard:
    number: str
    name: str
    strength: int
    agility: int
    fighting: int
    brains: int
    image_url: str

    table: str = 'cards_1'
    blur: bool = False
    greyscale: bool = False
    path: str = None

    @classmethod
    def from_row(cls, card_row: dict, table='cards_1'):
        return cls(
            number=card_row['card_number'],
            name=card_row['name'],
            strength=card_row['strength'],
            agility=card_row['agility'],
            fighting=card_row['fighting'],
            brains=card_row['brains'],
            image_url=card_row['image_url'],
            table=table,
            path=str(script_dir / 'img' / table / f'{card_row["name"]}.png'),
        )


@dataclass
class AbilityCard:
    number: str
    name: str
    effect_type: str
    effect_value: int
    target: str
    image_url: str

    table: str = 'cards_abilities_1'
    blur: bool = False
    greyscale: bool = False
    path: str = None

    @classmethod
    def from_row(cls, ability_row: dict, table='cards_abilities_1'):
        return cls(
            number=ability_row['card_number'],
            name=ability_row['name'],
            effect_type=ability_row['effect_type'],
            effect_value=ability_row['effect_value'],
            target=ability_row['target'],
            image_url=ability_row['image_url'],
            table=table,
            path=str(script_dir / 'img' / table / f'{ability_row["name"]}.png'),
        )


@dataclass
class Player:
    user_id: int
    user_name: str
    character: CharacterCard
    ability: Optional[AbilityCard] = None

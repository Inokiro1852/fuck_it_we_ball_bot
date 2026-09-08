from dataclasses import dataclass
from pathlib import Path

script_dir = Path(__file__).parent


@dataclass(kw_only=True)
class Card:
    number: str
    name: str
    image_url: str
    table: str
    blur: bool = False
    greyscale: bool = False
    path: str | None = None

    def get_attribute_and_number(self) -> str:
        if self.blur:
            return f'{self.number}_B'
        if self.greyscale:
            return f'{self.number}_G'
        return self.number


@dataclass(kw_only=True)
class CharacterCard(Card):
    strength: int
    agility: int
    fighting: int
    brains: int
    table: str = 'cards_1'

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


@dataclass(kw_only=True)
class AbilityCard(Card):
    effect_type: str
    effect_value: int
    target: str
    table: str = 'cards_abilities_1'

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


@dataclass(kw_only=True)
class Player:
    user_id: int
    user_name: str
    character: CharacterCard
    ability: AbilityCard | None = None

import asyncio
import logging
import os
import random
import sys
import uuid

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineQuery, InlineQueryResultArticle, InputTextMessageContent, \
    LinkPreviewOptions
from dotenv import load_dotenv

load_dotenv(".env")
BOT_TOKEN = os.environ.get('BOT_TOKEN')

dp = Dispatcher()

major_arcana = {
    "The Fool":
        "Ты вытянул... Шута 🪬\n\nВдох, выдох. Бездна лижет твои пятки. Не смотри вниз, доверься потолку.",
    "The Fool (Reversed)":
        "Ты вытянул... Шута (Перевёрнутая) 🪬\n\nНе бойся перемен, иначе они тебя сожрут.",

    "The Magician":
        "Ты вытянул... Мага 🪬\n\nУ тебя есть сила изменить мир. Но сперва начни менять себя. Твоя воля — закон.",
    "The Magician (Reversed)":
        "Ты вытянул... Мага (Перевёрнутая) 🪬\n\nТвои заклинания бьют по своим, сестра. Кастуй-ка хил.",

    "The High Priestess":
        "Ты вытянул... Верховную Жрицу 🪬\n\nТвоё сердце во мгле. Пролей же свет. Слушай топот тысячи коней.",
    "The High Priestess (Reversed)":
        "Ты вытянул... Верховную Жрицу (Перевёрнутая) 🪬\n\nТайное становится явным, и тебе сие не по нраву. Помни: зеркало врёт.",

    "The Empress":
        "Ты вытянул... Императрицу 🪬\n\nНесмотря на все неудачи, ты превозмог. Отдохни. Сегодня — время собирать урожай.",
    "The Empress (Reversed)":
        "Ты вытянул... Императрицу (Перевёрнутая) 🪬\n\nТвоя зона комфорта отравляет тебя более, нежели болото Бабадзаки. Про это ли ты мечтал?",

    "The Emperor":
        "Ты вытянул... Императора 🪬\n\nХватит ныть. Всё в твоих руках. Строй из себя хуй пойми что.",
    "The Emperor (Reversed)":
        "Ты вытянул... Императора (Перевёрнутая) 🪬\n\nНичего не работает? Похуй, адаптируйся.",

    "The Hierophant":
        "Ты вытянул... Иерофанта 🪬\n\nВелосипед шире изобретён. Проехали. Прислушайся к свыше.",
    "The Hierophant (Reversed)":
        "Ты вытянул... Иерофанта (Перевёрнутая) 🪬\n\nК чёрту правила, ебашь в хаосе.",

    "The Lovers":
        "Ты вытянул... Влюблённых 🪬\n\nВыбирай сердцем верный путь.",
    "The Lovers (Reversed)":
        "Ты вытянул... Влюблённых (Перевёрнутая) 🪬\n\nСоблазн велик, но велик распадётся на части. Не поддавайся искушению.",

    "The Chariot":
        "Ты вытянул... Колесницу  🪬\n\nТормоза придумали трусы. А трусы у тебя с дыркой. Жми на газ, еврей.",
    "The Chariot (Reversed)":
        "Ты вытянул... Колесницу  (Перевёрнутая) 🪬\n\nНе гоняйте, пацаны, матерям ещё нужны. Ожидай помощи.",

    "Strength":
        "Ты вытянул... Силу 🪬\n\nНе бей в лоб, используй мягкую лапу. Доброе словечко острее катаны.",
    "Strength (Reversed)":
        "Ты вытянул... Силу (Перевёрнутая) 🪬\n\nНе теряй себя из виду, иначе сам себе глотку перегрызёшь.",

    "The Hermit":
        "Ты вытянул... Отшельника 🪬\n\nИди потрогай траву. В одиночестве.",
    "The Hermit (Reversed)":
        "Ты вытянул... Отшельника (Перевёрнутая) 🪬\n\nТы не справишься сам. А самсара тебя поглотит.",

    "The Wheel of Fortune":
        "Ты вытянул... Колесо Фортуны 🪬\n\nОбретёшь способность найти удачу там, где ей и места не было.",
    "The Wheel of Fortune (Reversed)":
        "Ты вытянул... Колесо Фортуны (Перевёрнутая) 🪬\n\nПригнись, брат. Сзади Critical Failure.",

    "Justice":
        "Ты вытянул... Справедливость 🪬\n\nЧто посеял, то и жрёшь. А значит будь добр.",
    "Justice (Reversed)":
        "Ты вытянул... Справедливость (Перевёрнутая) 🪬\n\nМир несправедлив? Правда. Ведь Миру нужна Справедливость!",

    "The Hanged Man":
        "Ты вытянул... Повешенного 🪬\n\nЗашёл в ТУПИК? Измени подход. Решение всегда за УГЛОМ.",
    "The Hanged Man (Reversed)":
        "Ты вытянул... Повешенного (Перевёрнутая) 🪬\n\nХватит жертв. Пожертвуй своей жертвенностью.",

    "The Death":
        "Ты вытянул... Смерть 🪬\n\nПоздравляю! Тебе пиздец.",
    "The Death (Reversed)":
        "Ты вытянул... Смерть (Перевёрнутая) 🪬\n\nТруп прошлого никогда не оживёт. Отпусти. Сожги мосты.",

    "Temperance":
        "Ты вытянул... Умеренность 🪬\n\nКогда-то давно четыре народа жили в мире.",
    "Temperance (Reversed)":
        "Ты вытянул... Умеренность (Перевёрнутая) 🪬\n\nТы бежишь слишком быстро, чтобы заметить вещи, ради которых ты начал бегать.",

    "The Devil":
        "Ты вытянул... Дьявола 🪬\n\nПлохая идея. И ты это знаешь. Тебя это никогда не останавливало.",
    "The Devil (Reversed)":
        "Ты вытянул... Дьявола (Перевёрнутая) 🪬\n\nРутина вгрызается в плоть. Отруби (ха-ха) свои плохие привычки, пока жив.",

    "The Tower":
        "Ты вытянул... Башню 🪬\n\nТолько разрушив свой дом... Бляяя, нахуя я его разрушил.",
    "The Tower (Reversed)":
        "Ты вытянул... Башню (Перевёрнутая) 🪬\n\nВ горящем ДОМе чувствуешь себя УЮТно.",

    "The Star":
        "Ты вытянул... Звезду 🪬\n\nМрак вокруг. Но ты знаешь, как добраться домой. Всегда знал.",
    "The Star (Reversed)":
        "Ты вытянул... Звезду (Перевёрнутая) 🪬\n\nМечты кажутся пеплом, но это лишь пыль в глазах. Протри их.",

    "The Moon":
        "Ты вытянул... Луну 🪬\n\nНе верь лжи. Осязай правду.",
    "The Moon (Reversed)":
        "Ты вытянул... Луну (Перевёрнутая) 🪬\n\nХватит убегать. Взгляни в зеркало.",

    "The Sun":
        "Ты вытянул... Солнце 🪬\n\nПрикольно ебать. Забавно дрочить.",
    "The Sun (Reversed)":
        "Ты вытянул... Солнце (Перевёрнутая) 🪬\n\nЯсно. Ой, да нихуя не ясно.",

    "Judgement":
        "Ты вытянул... Суд 🪬\n\nЛучше звоните Солу!",
    "Judgement (Reversed)":
        "Ты вытянул... Суд (Перевёрнутая) 🪬\n\nПацаны, этот вагон отвезёт вас не в Бутово, а на Страшный Суд, где вы в полной мере ответите за свои мирские деяния.",

    "The World":
        "Ты вытянул... Мир 🪬\n\nПрокатил мир на карусели хуёв.",
    "The World (Reversed)":
        "Ты вытянул... Мир (Перевёрнутая) 🪬\n\nЧтоб пройти эту жизнь, тебе придётся трахнуть мир с ссанным пидором. Пока что, ссанный пидор — ты.",
}

faggots = {
    "faggot1":
        "Ты вытянул... Забывшего 🪬\n\n<tg-spoiler>ㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤㅤ</tg-spoiler>",

    "faggot2":
        "Ты вытянул... Фембоя 🪬\n\nС двумя членами получается очень охуенно.",

    "faggot3":
        "Ты вытянул... Фембоя (Перевёрнутая) 🪬\n\nТебя отпинали в переулке.",

    "faggot4":
        "Ты вытянул... Земноводного 🪬\n\nЧипсов со вкусом малосольных огурчиков, да Черноголовкой бы запить...",

    "faggot5":
        "Ты вытянул... Розу 🪬\n\nА я на них срал!",

    "faggot6":
        "Ты вытянул... Пекарню 🪬\n\nИди нахуй, сын садовника.",

    "faggot7":
        "Ты вытянул... Забывшего (Перевёрнутая) 🪬\n\nБудни это суббота и вс?",

    "faggot8":
        "Ты вытянул... Обжорство 🪬\n\nНа 8 человек сожрали 6 человек. Обычные будни в Казахстане.",

    "faggot9":
        "Ты вытянул... Гулистанца 🪬\n\n<tg-spoiler>Свет мой, зеркальце! скажи, да всю правду доложи: я ль на свете всех милее, всех румяней и белее?\nВыходит дева из избушки да заорёт: КТО ТАКОЙ БЛЯДЬ АЙТАПКИ КИД?!</tg-spoiler>",

    "faggot10":
        "Ты вытянул... Обжорство 🪬\n\nНа 8 человек сожрали 6 человек. Обычные будни в Казахстане.",

    "faggot11":
        "Ты вытянул... Роботизированного 🪬\n\nНет, Иноки, ты долбоёб.",

    "faggot12":
        "Ты вытянул... Пизду 🪬\n\n<tg-spoiler>Шапка*.</tg-spoiler>",
}

faggots_images = {
    "faggot1": ["Ты вытянул... Гулистанца (Перевёрнутая) 🪬",
                "https://i.redd.it/4a4qdq6l0jrf1.jpeg"],

    "faggot2": ["Ты вытянул... УМАлишённого 🪬",
                "https://i.pinimg.com/736x/5d/1b/69/5d1b6975e5e3ddcc5a9609816b00c3ab.jpg"],

    "faggot3": ["Ты вытянул... Разделение 🪬",
                "https://i.pinimg.com/736x/9c/1e/45/9c1e45ef5762bc91e67978745f253e11.jpg"],

    "faggot4": ["Ты вытянул... Бессмертие 🪬",
                "https://i.pinimg.com/736x/65/e9/26/65e9262c9fa124264c540ce1ac4ffd04.jpg"],

    "faggot5": ["Ты вытянул... Гулистанца 🪬",
                "https://i.pinimg.com/736x/74/8c/52/748c523274d384d6949fe983517c6094.jpg"],
}


async def random_arcana():
    chance = random.random()
    if chance < 0.5:
        return 1, random.choice(list(major_arcana))
    elif chance < 0.9:
        return 2, random.choice(list(faggots))
    else:
        return 3, random.choice(list(faggots_images))


@dp.message(CommandStart())
async def hello(message: Message) -> None:
    await message.answer(f"Fuck you, {message.from_user.first_name}!")


@dp.inline_query()
async def handle_all_inline_query(inline_query: InlineQuery) -> None:
    query = inline_query.query.strip()
    results = []

    # 1. prediction
    if not query.startswith("d"):
        prediction = await random_arcana()

        if prediction[0] == 1:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{major_arcana[prediction[1]]}",
                    )
                ))
        elif prediction[0] == 2:
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=f"{faggots[prediction[1]]}",
                    )
                ))
        else:
            photo_file_id = faggots_images[prediction[1]][1]
            caption_text = faggots_images[prediction[1]][0]
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your prediction 🎭",
                    description="Good luck!",
                    input_message_content=InputTextMessageContent(
                        message_text=caption_text,
                        link_preview_options=LinkPreviewOptions(
                            url=photo_file_id,
                            show_above_text=False,
                            is_disabled=False
                        )
                    )
                ))

    # 2. dice roll (custom)
    if query.startswith("d") and len(query) > 1:
        try:
            number = int(query[1:])
            results.append(
                InlineQueryResultArticle(
                    id=str(uuid.uuid4()),
                    title="Get your dice 🎲",
                    description=f"(d{number})",
                    input_message_content=InputTextMessageContent(
                        message_text=f"<code>(d{number})</code>: {random.randint(1, number)}",
                    )
                ))
        except ValueError:
            pass

    # 3. dice roll static
    if not query.startswith("d"):
        results.append(
            InlineQueryResultArticle(
                id=str(uuid.uuid4()),
                title="Get your dice 🎲",
                description="(d20)",
                input_message_content=InputTextMessageContent(
                    message_text=f"<code>(d20)</code>: {random.randint(1, 20)}",
                )
            ))

    await inline_query.answer(
        results=results,
        cache_time=0,
        is_personal=True,
    )


async def main() -> None:
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())

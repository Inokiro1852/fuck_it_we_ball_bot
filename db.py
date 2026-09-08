import aiosqlite

DB_CONN = None


async def on_startup():
    global DB_CONN
    DB_CONN = await aiosqlite.connect('tmnt.db')
    DB_CONN.row_factory = aiosqlite.Row


async def on_shutdown():
    await DB_CONN.close()


async def execute_query(
    query: str,
    params: tuple = (),
    fetch_one: bool = False,
    fetch_all: bool = False,
    commit: bool = False,
):
    async with DB_CONN.execute(query, params) as cursor:
        if commit:
            await DB_CONN.commit()
        if fetch_one:
            return await cursor.fetchone()
        if fetch_all:
            return await cursor.fetchall()


async def fetch_card(card_number: str, columns: list[str], table_name: str = 'cards_1'):
    if not columns:
        columns = ('image_url',)
    for column in columns:
        if not column.isidentifier():
            raise ValueError(f'Column "{column}" is not a valid identifier')

    if not table_name.isidentifier():
        raise ValueError(f'Table name "{table_name}" is not a valid identifier')

    columns_str = ', '.join(columns)
    return await execute_query(
        query=f'SELECT {columns_str} FROM {table_name} WHERE card_number = ?',
        params=(card_number,),
        fetch_one=True,
    )


async def fetch_random_card(table_name: str, limit: int = 1):
    fetch_args = {'fetch_one': True} if limit == 1 else {'fetch_all': True}
    return await execute_query(
        query=f'SELECT card_number, name, strength, agility, fighting, brains, image_url FROM {table_name} ORDER BY RANDOM() LIMIT ?',
        params=(limit,),
        **fetch_args,
    )


async def fetch_random_ability_card(table_name: str, limit: int = 1):
    fetch_args = {'fetch_one': True} if limit == 1 else {'fetch_all': True}
    return await execute_query(
        query=f'SELECT card_number, name, effect_type, effect_value, target, image_url FROM {table_name} ORDER BY RANDOM() LIMIT ?',
        params=(limit,),
        **fetch_args,
    )


async def image_url_exists(card_number: str, table_name: str):
    card = await fetch_card(card_number, [], table_name)
    if card is None:
        return False
    return card['image_url']


async def save_img_url(card_number_glued: str, image_url: str, table_name: str):
    await execute_query(
        query=f'INSERT INTO {table_name} (card_number, image_url) VALUES (?, ?)',
        params=(
            card_number_glued,
            image_url,
        ),
        commit=True,
    )

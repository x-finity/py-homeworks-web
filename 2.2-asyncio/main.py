import asyncio
import aiohttp
import datetime
from more_itertools import chunked
from models import init_orm, close_orm, Session, SwapiPeople

MAX_COROUTINES = 5
BASE_URL = 'https://swapi.py4e.com/api/people'
HERO_IDS = []

async def get_hero(hero_id, session):
    '''Получаем информацию о герое и преобразуем '''
    response = await session.get(f'{BASE_URL}/{hero_id}')
    response = await response.json()
    if 'detail' in response and response['detail'] == 'Not found':
        # print(f'Герой с id {hero_id} не найден')
        return
    keys_to_delete = []

    for k, v in response.items():
        if isinstance(v, list):
            response[k] = ', '.join(v)
        elif isinstance(v, str) and v.isnumeric() and k != 'mass':
            response[k] = int(v)
        elif v == 'unknown' or v == 'n/a' or v == 'none':
            response[k] = None
        if k in ['created', 'edited', 'url']:
            keys_to_delete.append(k)
    response['id'] = hero_id
    HERO_IDS.append(hero_id)
    # if response['mass'] == 'unknown':
    #     response['mass'] = -1
    for key in keys_to_delete:
        del response[key]
    # print(response)
    return response

async def insert_people(data: list[dict]):
    '''Добавляем информацию о героях в БД'''
    async with Session() as session:
        for d in data:
            if d is None:
                continue
            session.add(SwapiPeople(**d))
        await session.commit()

async def main():
    await init_orm()
    async with aiohttp.ClientSession() as session:
        for chunk in chunked(range(1,100), MAX_COROUTINES):
            coroutines = [get_hero(i, session) for i in chunk]
            result = await asyncio.gather(*coroutines)
            # print(result)
            task = asyncio.create_task(insert_people(result))
    tasks = asyncio.all_tasks()
    current_task = asyncio.current_task()
    tasks.remove(current_task)
    await asyncio.gather(*tasks)
    await close_orm()


if __name__ == '__main__':
    start = datetime.datetime.now()
    asyncio.run(main())
    print(datetime.datetime.now() - start)
    # print(len(HERO_IDS))
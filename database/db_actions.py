import asyncio
import logging
import os
import sys
from typing import Union

from sqlalchemy import select, Select, update, Update, ChunkedIteratorResult
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine

from dotenv import load_dotenv

from tg_bot.utils.config import numeric_system_level, define_status
from database.db_structure import Base, AccountInfoLast, UserInfoLast, Users, Accounts

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(filename='sqlalchemy.log', level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.warning('Watch out!')

# Define a custom logger for SQLAlchemy
logger = logging.getLogger('sqlalchemy.engine')
logger.setLevel(logging.INFO)

root = logging.getLogger()
handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)


# async def db_insert(session: AsyncSession, table: Base, fresh_data: [list[dict], None] = None, **data) -> None:
#     if fresh_data:  # if multiple rows
#         data = fresh_data
#     # TODO: it will not work if fresh_data = None
#     stmt: Insert = insert(table).values(data)#.returning(table)#.prefix_with('IGNORE')
#     result = await session.execute(stmt)
#     print(f'result: {result}')
#     await session.commit()
#     return result.lastrowid


async def db_add_all(session: AsyncSession, table: Base = None, fresh_data: list[dict[str, None]] = [{}],
                     orm_objs: list[Base] = None, **common_columns_values) -> Union[list[Base], Base, None]:
    """
    Insert multiple rows of data or a single row into the database table.
    If many data, use: fresh_data/orm_objs, if only one row: **common_columns_values
    """
    if not orm_objs:
        orm_objs: list[Base] = [table(**common_columns_values, **sample) for sample in fresh_data]

    session.add_all(orm_objs)
    await session.commit()
    # return an object | None if one or list of objects
    return orm_objs[0] if len(orm_objs) == 1 else orm_objs


async def db_update(session: AsyncSession, table: Base, fresh_values: dict, **filter_by) -> None:
    """Update rows in the database table with new values."""
    # TODO: user merge here?
    stmt: Update = update(table).filter_by(**filter_by).values(**fresh_values)  # .prefix_with('IGNORE')
    await session.execute(stmt)
    await session.commit()


async def db_select(session: AsyncSession, table: Base, filters: list = [], order_by: list = [], **filter_by) \
        -> Union[list[Base, None], Base]:
    """Retrieve rows from the database table based on filters and conditions."""
    stmt: Select = select(table).filter(*filters).filter_by(**filter_by).order_by(*order_by)
    respond = await session.execute(stmt)
    result = respond.all()
    # TODO: (?) here can be a problem if we join tables and 'result' will be a [(obj_1, obj_2), ...], but not one obj.
    if len(result) != 1:
        return [row[0] for row in result]
    return result[0][0]


async def db_select_last_info(session: AsyncSession, table: Base, **fk_id)\
        -> dict[str: [AccountInfoLast, UserInfoLast], None]:
    """Retrieve the information from InfoLast tables based on foreign key ID."""
    # fk_id - foreign key id in the DB table: {account_ID/user_ID/event_ID: id}
    # table: AccountInfoLast, UserInfoLast, EventInfoLast, ...
    stmt: Select = select(table).filter_by(**fk_id)
    respond: ChunkedIteratorResult = await session.execute(stmt)
    # info_last = {feature: obj}
    info_last: dict[str: [AccountInfoLast, UserInfoLast], None] = \
        {obj[0].feature: obj[0] for obj in respond.all()}
    return info_last


# All functions below are derivatives from upper functions

async def db_merge_last_info(session: AsyncSession,
                             table: [AccountInfoLast, UserInfoLast],
                             orm_objs: list[dict[str: [AccountInfoLast, UserInfoLast]], None],
                             fresh_data: dict[str: [str, int, float]], **fk_id) -> None:
    # update all previous data
    for feature, obj in orm_objs.items():
        # can be optimized:
        if feature in fresh_data:
            # TODO: Error: PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (asyncmy.errors.IntegrityError) (1062, "Duplicate entry '1-84-expectation-Хочу понять уровень тре...' for key 'unique_index'")
            #  [SQL: INSERT INTO experience (`event_ID`, `user_ID`, feature, value) VALUES (%s, %s, %s, %s)]
            #  [parameters: (1, 84, 'expectation', 'Хочу понять уровень требований')]
            #  Is works?: Поторно - нет. Но в первый раз я получил сообщение, что зарегистрирован
            #  orm_tg_account: [<database.db_structure.Accounts object at 0x7fd745e925d0>, <database.db_structure.Accounts object at 0x7fd745e92610>]

            obj = await session.merge(obj)  # bound object to the session
            obj.value = fresh_data.pop(feature)
    await session.commit()

    if fresh_data:  # if something new to add to DB
        new_orm_objects = []  # pool to send all new objects to the DB
        for feature, value in fresh_data.items():  # if new data exist for DB
            # create a data sample follow data structure of the table
            data = {**fk_id, 'feature': feature, 'value': value}
            # create a sample of the table
            orm_sample = table(**data)
            # add to the pool of new objects to send that to the DB
            new_orm_objects.append(orm_sample)
            # add the new orm_obj to old orm_obj, refresh it
            orm_objs[feature] = orm_sample
        await db_add_all(session, orm_objs=new_orm_objects)


async def orm_user_and_account(session: AsyncSession, tg_id: [int, str], is_bot: bool)\
        -> dict[str: [Users, Accounts]]:
    # searching the account & user in DB
    if orm_tg_account := await db_select(session, table=Accounts, in_app_id=tg_id):
        print(f'orm_tg_account: {orm_tg_account}')
        orm_user: Users = await db_select(session, table=Users, id=orm_tg_account.user_ID)
        # TODO: Error: katushkainduktivnosti & Alexandra Tokaeva & zhaksylykov23
        #  : id=orm_tg_account.user_ID): AttributeError: 'list' object has no attribute 'user_ID'
    else:  # create the account & user for the speaker in DB
        status = define_status(tg_id)
        orm_user: Users = Users(status=status, system_level=numeric_system_level[status])
        orm_tg_account: Accounts = Accounts(user=orm_user, name_app='tg', in_app_id=tg_id, is_bot=is_bot)
        await db_add_all(session, orm_objs=[orm_tg_account])  # not separately add 'orm_user' as it in 'orm_tg_account'
    return {'user': orm_user, 'account': orm_tg_account}

  # File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/utils/data_structure.py", line 36, in create
  #   orm: dict[str: [Users, Accounts]] = await orm_user_and_account(session, tg_id=tg_user.id, is_bot=tg_user.is_bot)
  #                                       ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  # File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/database/db_actions.py", line 123, in orm_user_and_account
  #   async def orm_user_and_account(session: AsyncSession, tg_id: [int, str], is_bot: bool)\
  #                                                                      ^^^^^^^^^^^^^^^^^^^^
async def main() -> None:
    url = f"{os.environ.get('databaseSystem')}+{os.environ.get('databaseDBAPIasync')}://" \
          f"{os.environ.get('databaseUser')}:{os.environ.get('databaseKey')}" \
          f"@{os.environ.get('databaseIP')}:{os.environ.get('databasePort')}/"

    engine: AsyncEngine = create_async_engine(url + os.environ.get('database'), future=True, echo=False)
    session_pool = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    async with session_pool() as session:
        pass


if __name__ == '__main__':
    asyncio.run(main())

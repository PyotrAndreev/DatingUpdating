import asyncio
import os

from aiogram import Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession, AsyncEngine

from tg_bot.data_structure import bot
from tg_bot.init import CustomMiddleware, menu_commands

from tg_bot.stages.start_menu import router as start_menu
from tg_bot.stages.report import router as report
from tg_bot.stages.refresh_token.order_routers import refresh_token
from tg_bot.stages.set_filters.set_filters import router as set_filters
from tg_bot.stages.client_apps.order_routers import client_apps
from tg_bot.stages.message_delete import router as del_user_message


url = f"{os.environ.get('databaseSystem')}+{os.environ.get('databaseDBAPIasync')}://" \
      f"{os.environ.get('databaseUser')}:{os.environ.get('databaseKey')}" \
      f"@{os.environ.get('databaseIP')}:{os.environ.get('databasePort')}/"
# f"{os.environ.get('databaseSystem')}+{os.environ.get('databaseDBAPI')}://" \

storage = MemoryStorage()  # client data storage (cleaned after program was stopped)
dp = Dispatcher(storage=storage)


async def main():
    # Creating DB engine
    engine: AsyncEngine = create_async_engine(url + os.environ.get('database'), future=True, echo=False,
                                              max_overflow=-1,
                                              pool_recycle=30 * 60)  # recycle connections after 30 minutes
                                              # request_timeout = 60
    # the router order refresh_token is strongly important
    dp.include_routers(start_menu, report)
    dp.include_routers(*refresh_token)
    dp.include_router(set_filters)
    dp.include_router(*client_apps)

    dp.include_router(del_user_message)

    # expire_on_commit - don't expire objects after transaction commit
    # Creating DB connections pool
    db_pool = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    dp.update.middleware(CustomMiddleware(db_pool))

    # Register /-commands in UI
    await bot.set_my_commands(menu_commands)
    await bot.delete_webhook(drop_pending_updates=True)  # don't respond to collected updates (when bot didn't work)
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
    # asyncio.run(test())
    # new_data_to_add: list[dict] = [table(**fk_id, feature=key, value=B[key]) for key in B if key not in A]
    # print(f'new_data_rows: {new_data_to_add}')

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types.user import User as AiogramUser
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from database.db_actions import db_select, db_select_last_info, db_merge_last_info, db_add_all, orm_user_and_account
from database.db_structure import Accounts, Users, AccountInfoLast, UserInfoLast, Experience, BotInteraction, Reports
from tg_bot.utils.find_user_tg_id import find_tg_id


class DBUser(object):
    def __init__(self, session: AsyncSession, tg_user: AiogramUser,
                 orm_user: Users, orm_user_info: dict[str: UserInfoLast, None],
                 orm_tg_account: Accounts, orm_tg_account_info: dict[str: AccountInfoLast, None]) -> None:
        self.session: AsyncSession = session
        self.id: int = tg_user.id
        self.first_name: str = tg_user.first_name

        self.orm_user: Users = orm_user
        self.orm_user_info: dict[str: UserInfoLast, None] = orm_user_info
        self.orm_tg_account: Accounts = orm_tg_account
        self.orm_tg_account_info: dict[str: AccountInfoLast, None] = orm_tg_account_info

        self.chosen_event_id: [int, None] = None

        self.report_type: [str, None] = None
        self.bot_interaction_id: [int, None] = None

    @staticmethod
    async def create(session: AsyncSession, tg_user: AiogramUser):  # -> DBUser
        # TODO:   File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/utils/data_structure.py", line 36, in create
        #     orm: dict[str: [Users, Accounts]] = await orm_user_and_account(session, tg_id=tg_user.id, is_bot=tg_user.is_bot)
        #                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #   File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/database/db_actions.py", line 123, in orm_user_and_account
        #     async def orm_user_and_account(session: AsyncSession, tg_id: [int, str], is_bot: bool)\
        #                                                                        ^^^^^^^^^^^^^^^^^^^^
        orm: dict[str: [Users, Accounts]] = await orm_user_and_account(session, tg_id=tg_user.id, is_bot=tg_user.is_bot)
        orm_user: Users = orm['user']
        orm_tg_account: Accounts = orm['account']

        orm_user_info: UserInfoLast = await db_select_last_info(session, table=UserInfoLast, user_ID=orm_user.id)
        orm_tg_account_info: AccountInfoLast = await db_select_last_info(session, table=AccountInfoLast,
                                                                         account_ID=orm_tg_account.id)
        user: DBUser = DBUser(session, tg_user=tg_user, orm_user=orm_user, orm_user_info=orm_user_info,
                              orm_tg_account=orm_tg_account, orm_tg_account_info=orm_tg_account_info)
        return user

    async def update_user_last_info(self, fresh_data: dict[str: [str, int, float]]) -> None:
        await db_merge_last_info(self.session, table=UserInfoLast, orm_objs=self.orm_user_info,
                                 fresh_data=fresh_data, user_ID=self.orm_user.id)

    async def update_account_last_info(self, fresh_data: dict[str: [str, int, float]]) -> None:
        # TODO: Error: PendingRollbackError: This Session's transaction has been rolled back due to a previous exception during flush. To begin a new transaction with this Session, first issue Session.rollback(). Original exception was: (asyncmy.errors.IntegrityError) (1062, "Duplicate entry '1-84-expectation-Хочу понять уровень тре...' for key 'unique_index'")
        #  [SQL: INSERT INTO experience (`event_ID`, `user_ID`, feature, value) VALUES (%s, %s, %s, %s)]
        #  [parameters: (1, 84, 'expectation', 'Хочу понять уровень требований')]
        #  Is works?: Поторно - нет. Но в первый раз я получил сообщение, что зарегистрирован
        await db_merge_last_info(self.session, table=AccountInfoLast, orm_objs=self.orm_tg_account_info,
                                 fresh_data=fresh_data, account_ID=self.orm_tg_account.id)

    async def send_report(self, text: str, tg_user: AiogramUser) -> None:
        await db_add_all(self.session, table=Reports,
                         account_ID=self.orm_tg_account.id, bot_interaction_ID=self.bot_interaction_id,
                         feature=self.report_type, value=text)
        # TODO: fix: bellow can not be username
        await bot.send_message(chat_id=tg_user.id,
                               text=f'New report: {self.report_type}\n'
                                    f'from <a href=https://t.me/{tg_user.username}>{tg_user.full_name}</a>\n\n'
                                    f'text:\n'
                                    f'{text}',
                               # TODO: text: return approximately 10 previous steps with results
                               parse_mode='HTML')

    async def log_user_action(self, update_id: [str, int], event_type: str, message_id: [str, int], event_data: str) \
            -> None:
        orm_objs = await db_add_all(self.session, table=BotInteraction, account_ID=self.orm_tg_account.id,
                                    update_id=update_id, event=event_type, message_id=message_id, data=event_data)
        self.bot_interaction_id = orm_objs.id


class UserWorkflow(object):
    """need to edit a message and show to user a bot stage"""

    def __init__(self, tg_user_id: int):
        self.chat_id: int = tg_user_id  # is tg_user_id
        self.chat_messages: list[int] = []  # mes_id: messages what are in chat
        self.useless_messages: list[int] = []  # messages to delete after
        self.useless_keyboard: int or None = None  # keyboard to delete on the next step
        self.edit_message: int or None = None  # message to edit on the next step

        # TODO: find better way to throw data
        self.keep_data_name: [str, None] = None

    def store_message(self, mes_id):  # to add all at the ends
        self.chat_messages.append(mes_id)

    def add_to_delete_queue(self, messages_id: list):
        self.useless_messages.extend(messages_id)

    async def del_useless_messages(self):
        for mes_id in self.useless_messages:
            await bot.delete_message(chat_id=self.chat_id,
                                     message_id=mes_id)
            if mes_id in self.chat_messages:
                self.chat_messages.remove(mes_id)  # del from the message pool
        self.useless_messages.clear()

    async def del_keyboard(self):
        if self.useless_keyboard:
            await bot.edit_message_reply_markup(chat_id=self.chat_id,
                                                message_id=self.useless_keyboard)
        self.useless_keyboard = None

    # async def del_all_messages(self, chat_id):


@dataclass
class TgData:
    DBUser: DBUser
    UserWorkflow: UserWorkflow


users: dict[int: TgData] = {}  # dict where {tg_user.id: TgData(User(..), UserWorkflow(...)),  ...}

bot = Bot(token=os.environ.get('tgbotToken'))

if __name__ == '__main__':
    async def main():
        url = f"{os.environ.get('databaseSystem')}+{os.environ.get('databaseDBAPIasync')}://" \
              f"{os.environ.get('databaseUser')}:{os.environ.get('databaseKey')}" \
              f"@{os.environ.get('databaseIP')}:{os.environ.get('databasePort')}/"

        engine: AsyncEngine = create_async_engine(url + os.environ.get('database'), future=True, echo=False)
        session_pool = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

        async with session_pool() as session:
            pass

    asyncio.run(main())

import asyncio
import os
from dataclasses import dataclass
from datetime import datetime, timedelta

from aiogram import Bot
from aiogram.types.user import User as AiogramUser
from sqlalchemy.ext.asyncio import AsyncSession, AsyncEngine, create_async_engine, async_sessionmaker

from database.db_actions import db_select_last_info, db_merge_last_info, db_add_all, orm_user_and_accounts, db_update, \
    db_select
from database.db_structure import Accounts, Users, AccountInfoLast, UserInfoLast, BotInteraction, Reports, ClientApps, \
    MessageTemplates
from tg_bot.utils.notify_support_team import notify_support_team
from tg_bot.utils.respons_wrapper import prepare_data_to_db
from tinder.phone_auth import send_sms_code, get_tinder_token, get_api_token


class DBUser(object):
    def __init__(self, session: AsyncSession, tg_user: AiogramUser,
                 orm_user: Users, orm_user_info: dict[str: UserInfoLast] | None,
                 orm_tg_account: Accounts, orm_tg_account_info: dict[str: AccountInfoLast | None],
                 orm_tinder_account: Accounts, orm_tinder_account_info: dict[str: AccountInfoLast | None]) -> None:
        self.session: AsyncSession = session
        self.id: int = tg_user.id
        self.first_name: str = tg_user.first_name

        self.orm_user: Users = orm_user
        self.orm_user_info: dict[str: UserInfoLast | None] = orm_user_info

        self.orm_tg_account: Accounts = orm_tg_account
        self.orm_tg_account_info: dict[str: AccountInfoLast | None] = orm_tg_account_info

        self.orm_tinder_account: Accounts = orm_tinder_account
        self.orm_tinder_account_info: dict[str: AccountInfoLast | None] = orm_tinder_account_info

        self.report_type: str | None = None
        self.bot_interaction_id: int | None = None

        self.received_phones: dict[str: int] = {}  # {phone: n_sms_codes_sent, ...}

        self.orm_message_template: MessageTemplates | None = None

    @staticmethod
    async def create(session: AsyncSession, tg_user: AiogramUser):  # -> DBUser
        # TODO:   File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/utils/data_structure.py", line 36, in create
        #     orm: dict[str: [Users, Accounts]] = await orm_user_and_account(session, tg_id=tg_user.id, is_bot=tg_user.is_bot)
        #                                         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        #   File "/home/petr/PycharmProjects/home/petr/PycharmProjects/RegistrationBot/database/db_actions.py", line 123, in orm_user_and_account
        #     async def orm_user_and_account(session: AsyncSession, tg_id: [int, str], is_bot: bool)\
        #                                                                        ^^^^^^^^^^^^^^^^^^^^
        orm: dict[str: [Users, Accounts]] = await orm_user_and_accounts(session, tg_id=tg_user.id,
                                                                        is_bot=tg_user.is_bot)
        orm_user: Users = orm['user']
        orm_user_info: UserInfoLast = await db_select_last_info(session, table=UserInfoLast, user_ID=orm_user.id)

        orm_tg_account: Accounts = orm['tg_account']
        orm_tg_account_info: dict[str: AccountInfoLast | None] = \
            await db_select_last_info(session, table=AccountInfoLast, account_ID=orm_tg_account.id)

        orm_tinder_account: Accounts = orm['tinder_account']
        if orm_tinder_account:
            orm_tinder_account_info: dict[str: AccountInfoLast | None] = \
                await db_select_last_info(session, table=AccountInfoLast, account_ID=orm_tinder_account.id)
        else:  # as a tinder account can be not register
            orm_tinder_account_info = {}

        user: DBUser = DBUser(session, tg_user=tg_user, orm_user=orm_user, orm_user_info=orm_user_info,
                              orm_tg_account=orm_tg_account, orm_tg_account_info=orm_tg_account_info,
                              orm_tinder_account=orm_tinder_account, orm_tinder_account_info=orm_tinder_account_info)
        return user

    async def add_sms_attempt(self, phone: str) -> dict:
        if not self.received_phones.get(phone):
            self.received_phones[phone] = 0
        self.received_phones[phone] += 1
        response: dict = await send_sms_code(phone)  # send sms code from Tinder to the client

        await db_merge_last_info(self.session, table=AccountInfoLast, orm_objs=self.orm_tinder_account_info,
                                 fresh_data={'phone': phone, **prepare_data_to_db(response, prefix='otp')},
                                 account_ID=self.orm_tinder_account.id)
        return response

    async def ask_tinder_refresh_token(self, code: int) -> dict:
        last_phone: str = self.orm_tinder_account_info.get('phone').value

        if not last_phone:
            raise print("?!? where is a phone in 'orm_tinder_account' ?!? look into 'db_structure.py':'ask_tinder_refresh_token'")

        response: dict = await get_tinder_token(sms_code=code, phone_number=last_phone)

        # save the code in local machin and in DB & response in DB
        await db_merge_last_info(self.session, table=AccountInfoLast, orm_objs=self.orm_tinder_account_info,
                                 fresh_data={'otp_code': code, **prepare_data_to_db(response, prefix='refresh_token')},
                                 account_ID=self.orm_tinder_account.id)
        return response

    async def ask_tinder_api_token(self) -> dict:
        refresh_token: str = self.orm_tinder_account_info.get('refresh_token').value

        if not refresh_token:
            raise print(
                "?!? where is a phone in 'orm_tinder_account' ?!? look into 'db_structure.py':'ask_tinder_refresh_token'")

        response: dict = await get_api_token(refresh_token)

        if tinder_id := response.get('data', {}).get('_id'):
            # TODO: input the below into a function and use from 'db_actions.py'
            await self.session.merge(self.orm_tinder_account)  # bound object to the session
            self.orm_tinder_account.in_app_id = tinder_id
            await self.session.commit()
        # save the code in local machin and in DB & response in DB
        await db_merge_last_info(self.session, table=AccountInfoLast, orm_objs=self.orm_tinder_account_info,
                                 fresh_data={**prepare_data_to_db(response, prefix='api_token')},
                                 account_ID=self.orm_tinder_account.id)
        return response

    # async def take_message_template(self):
    #     # take the last inserted template
    #     self.orm_message_template = await db_select(self.session, table=MessageTemplates,
    #                                                 account_ID=self.orm_tg_account.id,
    #                                                 order_by=[MessageTemplates.insert_time.desc()])
    #     return self.orm_message_template

    async def save_message_template(self, text):
        # if orm_client_app := await db_select(self.session, table=ClientApps, account_ID=self.orm_tg_account.id):
        #     orm_message_template =
        # else:
        #     orm_client_app: ClientApps = ClientApps(user_Id=self.orm_user.id, account_ID=self.orm_tg_account.id)
        self.orm_message_template = await db_select(self.session, table=MessageTemplates,
                                                    account_ID=self.orm_tg_account.id, template=text)
        if not self.orm_message_template:
            self.orm_message_template = MessageTemplates(account_ID=self.orm_tg_account.id, template=text)
            await db_add_all(self.session, orm_objs=[self.orm_message_template])

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
        await notify_support_team(report=True, text=text, report_type=self.report_type)
        # TODO: text: return approximately 10 previous steps with results

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

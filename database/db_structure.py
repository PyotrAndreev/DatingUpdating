import hashlib
import os
import re
from datetime import datetime

from dotenv import load_dotenv

from sqlalchemy.orm import declarative_base, relationship, Mapped, declared_attr
from sqlalchemy.sql import func, text
from sqlalchemy import create_engine, \
    UniqueConstraint, ForeignKey, Column, Boolean, Integer, Float, String, Text, Date, DateTime, Enum, JSON, Time

# TODO: add table Settings:
#    if you want to allow users to customize their experience with the bot,
#    you could create a table to store user settings such as notification preferences or display preferences.

charset = 'utf8mb4'
# collate: to optimise capacity (especially 'InfoHist') use 'nopad' utf8mb4_general_nopad_ci, but less in insert
collate = 'utf8mb4_general_ci'

# Load environment variables from .env file
load_dotenv()

url = f"{os.environ.get('databaseSystem')}+{os.environ.get('databaseDBAPI')}://" \
      f"{os.environ.get('databaseUser')}:{os.environ.get('databaseKey')}" \
      f"@{os.environ.get('databaseIP')}:{os.environ.get('databasePort')}/"

# create a server engine to crete DB
engine = create_engine(url, echo=False)

# create the database if it doesn't exist
with engine.connect() as conn:
    create_query = f"CREATE DATABASE IF NOT EXISTS {os.environ.get('database')} DEFAULT CHARACTER SET {charset} COLLATE {collate}"
    conn.execute(text(create_query))

# create a server engine to crete tables in the DB
engine = create_engine(url + os.environ.get('database'), echo=False)


def camel_to_snake(name):
    """
    Convert camel case string to snake case string
    """
    name = re.sub(r'(?<!^)(?=[A-Z])', '_', name).lower()
    return name


class CustomBase(object):
    # TODO: order columns: id, (other columns of a table), insert_time
    id: Mapped[Integer] = Column(Integer, nullable=False, primary_key=True, autoincrement=True)
    insert_time = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())

    @declared_attr
    def __tablename__(cls):
        return camel_to_snake(cls.__name__)


Base = declarative_base(cls=CustomBase)


class UserInfoLast(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    value: str = Column(String(500), default='None', nullable=False)  # None - not value
    # insert_time is insert_time of ..._last table (look into a trigger)

    __table_args__ = (
        UniqueConstraint('user_ID', 'feature', 'value', name='unique_index'),
    )

    user = relationship("Users", back_populates="user_info_last")


class UserInfoHist(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    value: str = Column(String(500), default='None', nullable=False)  # None - not value
    # insert_time is insert_time of ..._last table (look into a trigger)

    user = relationship("Users", back_populates="user_info_hist")


class Users(Base):
    status: str = Column(String(20), nullable=False)
    system_level: int = Column(Integer, nullable=False)  # look to config.py
    # TODO: what one more column should I input to differ people ?

    user_info_last = relationship("UserInfoLast", back_populates="user")
    user_info_hist = relationship("UserInfoHist", back_populates="user")
    accounts = relationship("Accounts", back_populates="user")

    subscriptions = relationship("Subscriptions", back_populates='user')
    # registrations = relationship("Registrations", back_populates="user")
    payments = relationship("Payments", back_populates="user")

    experience = relationship("Experience", back_populates="user")
    client_apps = relationship("ClientApps", back_populates="user")

    # payments = relationship("Payments", back_populates="user")


class Reports(Base):
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    # client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'), nullable=False)
    bot_interaction_ID: int = Column(Integer, ForeignKey('bot_interaction.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    value: str = Column(Text, nullable=False)

    # unique index is not need as 2 the same reports impossible if client didn't send twice
    # TODO: (out of the db module) make client restriction: 1 report per 1 minute (anti DOS attack)

    account = relationship("Accounts", back_populates="reports")
    # client_app = relationship("ClientApps", back_populates="reports")
    bot_interaction = relationship("BotInteraction", back_populates="report")


class AccountInfoLast(Base):
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    position: int = Column(Integer, default=0,
                           nullable=False)  # if data was deleted from position(= no data) -> check it in python
    value: str = Column(String(500), default='None', nullable=False)  # None - not value

    __table_args__ = (
        UniqueConstraint('account_ID', 'feature', 'position', 'value', name='unique_index'),
    )

    account = relationship("Accounts", back_populates="account_info_last")


class AccountInfoHist(Base):
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    position: int = Column(Integer, default=0, nullable=False)  # 0 - not position
    value: str = Column(String(500), default='None', nullable=False)  # None - not value
    # insert_time is insert_time of ..._last table (look into a trigger)

    account = relationship("Accounts", back_populates="account_info_hist")


class Accounts(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    name_app: str = Column(Enum('message', 'vk', 'tg', 'inst', 'tinder', 'None'), nullable=False)  # can be scalable
    in_app_id: str = Column(String(50), nullable=False)  # account id lengths: tinder 24 (str); tg 9 (int)
    is_bot: bool = Column(Boolean, default=False, nullable=False)

    __table_args__ = (
        # composite unique key as 'in_app_id' can be the same in 2 apps and 2
        UniqueConstraint('user_ID', 'name_app', 'in_app_id', name='unique_index'),
    )

    user = relationship("Users", back_populates="accounts")
    client_apps = relationship("ClientApps", back_populates="account")
    bot_interactions = relationship("BotInteraction", back_populates="account")
    reports = relationship("Reports", back_populates="account")


    account_info_last = relationship("AccountInfoLast", back_populates="account")
    account_info_hist = relationship("AccountInfoHist", back_populates="account")
    tin_available_param_last = relationship("TinAvailableParamLast", back_populates="account")
    tin_available_param_hist = relationship("TinAvailableParamHist", back_populates="account")

    message_templates = relationship("MessageTemplates", back_populates="account")
    sent_messages = relationship("SentMessages", back_populates="from_account",
                                 foreign_keys='SentMessages.from_account_ID')
    received_messages = relationship("SentMessages", back_populates="to_account",
                                     foreign_keys='SentMessages.to_account_ID')
    relations_sent = relationship("Relations", back_populates="from_account", foreign_keys='Relations.from_account_ID')
    relations_received = relationship("Relations", back_populates="to_account", foreign_keys='Relations.to_account_ID')

    sent_notifications = relationship("Notifications", back_populates="sender_account",
                                      foreign_keys='Notifications.sender_account_ID')
    received_notifications = relationship("Notifications", back_populates="to_account",
                                          foreign_keys='Notifications.to_account_ID')


class BotInteraction(Base):
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    update_id: int = Column(Integer, nullable=False)
    event: str = Column(String(50), nullable=False)
    message_id: int = Column(Integer, nullable=True)
    data: str = Column(String(1000), nullable=True)  # data, if user sent it

    account = relationship("Accounts", back_populates="bot_interactions")
    report = relationship("Reports", back_populates="bot_interaction")


class Notifications(Base):
    # TODO: ! Need be create log_notifications/hist_notifications + notifications, where will be texts
    # TODO: how can I send pool, and how can I input info to DB ?
    sender_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    to_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    feature: str = Column(String(50), nullable=False)
    value: str = Column(String(1000), nullable=False)  # data, if user sent it

    sender_account = relationship("Accounts", back_populates="sent_notifications", foreign_keys=[sender_account_ID])
    to_account = relationship("Accounts", back_populates="received_notifications", foreign_keys=[to_account_ID])


class MessageTemplates(Base):
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    # TODO: add two columns 'order', 'template_name'; add opportunity edit templates
    template: str = Column(String(700), nullable=False)

    __table_args__ = (
        UniqueConstraint('account_ID', 'template', name='unique_index'),
    )

    account = relationship("Accounts", back_populates="message_templates")
    sent_messages = relationship("SentMessages", back_populates="template")
    client_apps = relationship("ClientApps", back_populates="message_template")



class SentMessages(Base):
    # client_app_ID has <default=None/0> as can be done out of any client app
    client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'), default=0)
    from_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    to_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    template_ID: int = Column(Integer, ForeignKey('message_templates.id'), default='None', nullable=False)
    # 'None' - sent without template or received

    type: str = Column(Enum('message', 'vk', 'tg', 'inst'), nullable=False)  # can be scalable
    message: str = Column(Text, default='None')  # Not None/NULL, as in DB NULL==NULL: False, what makes duplicates
    # location =
    # Q:
    #  can we extract location. In previous DB we don't have location notes?
    send_date = Column(DateTime, default=0)  # 0 - not DataTime

    __table_args__ = (
        UniqueConstraint('client_app_ID', 'from_account_ID', 'to_account_ID', 'send_date', name='unique_index'),
    )

    client_app = relationship("ClientApps", back_populates="messages")
    from_account = relationship("Accounts", back_populates="sent_messages", foreign_keys=[from_account_ID])
    to_account = relationship("Accounts", back_populates="received_messages", foreign_keys=[to_account_ID])
    template = relationship("MessageTemplates", back_populates="sent_messages")


class Relations(Base):
    # client_app_ID has <default=None/0> as can be done out of any client app
    client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'), default=0)
    from_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    to_account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    relation_stage = Column(Enum('like', 'dislike', 'skip', 'match', 'block', 'report'),
                            nullable=False)  # can be scalable
    # location =
    # Q:
    #  can we extract location. In previous DB we don't have location notes?
    creation_time = Column(DateTime, default=0)  # 0 - not DataTime

    __table_args__ = (
        UniqueConstraint('client_app_ID', 'from_account_ID', 'to_account_ID', 'creation_time', name='unique_index'),
    )

    client_app = relationship("ClientApps", back_populates="relations")
    from_account = relationship("Accounts", back_populates="relations_sent", foreign_keys=[from_account_ID])
    to_account = relationship("Accounts", back_populates="relations_received", foreign_keys=[to_account_ID])


class TinAvailableParamLast(Base):
    """only for clients"""
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    tin_available_param_ID: int = Column(Integer, ForeignKey('tin_available_params.id'), nullable=False)

    __table_args__ = (
        UniqueConstraint('account_ID', 'tin_available_param_ID', name='unique_index'),
    )
    account = relationship("Accounts", back_populates="tin_available_param_last")
    available_params = relationship("TinAvailableParams", back_populates="last")


class TinAvailableParamHist(Base):
    """only for clients"""
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), nullable=False)
    tin_available_param_ID: int = Column(Integer, ForeignKey('tin_available_params.id'), nullable=False)
    # insert_time is insert_time of ..._last table (look into a trigger)

    account = relationship("Accounts", back_populates="tin_available_param_hist")
    available_params = relationship("TinAvailableParams", back_populates="history")


class TinAvailableParams(Base):
    param: str = Column(String(50), nullable=False)  # pets, passions, ...
    json_data: JSON = Column(JSON, nullable=False)
    hash: str = Column(String(length=64), index=True, nullable=False, unique=True)  # param, data

    def __init__(self, param, json_data):
        self.param = param
        self.json_data = json_data
        # calculate hash via 'param' & 'data'
        self.hash = hashlib.sha256(param.encode('utf-8') + json_data.encode('utf-8')).hexdigest()

    last = relationship("TinAvailableParamLast", back_populates="available_params")
    history = relationship("TinAvailableParamHist", back_populates="available_params")


class ClientApps(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    account_ID: int = Column(Integer, ForeignKey('accounts.id'), default=0)  # 0 - if we didn't receive token
    message_template_ID: int = Column(Integer, ForeignKey('message_templates.id'), default='None')
    # insert_time is insert_time of ..._last table (look into a trigger)

    # without 'UniqueConstraint' as one account can have many apps

    user = relationship("Users", back_populates="client_apps")
    account = relationship("Accounts", back_populates="client_apps")
    payments = relationship("Payments", back_populates="client_app")
    # reports = relationship("Reports", back_populates="client_app")

    filter_last = relationship("FilterLast", back_populates="client_app")
    filter_hist = relationship("FilterHist", back_populates="client_app")
    message_template = relationship("MessageTemplates", back_populates="client_apps")

    messages = relationship("SentMessages", back_populates="client_app")
    relations = relationship("Relations", back_populates="client_app")


class FilterLast(Base):
    client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'))
    feature: str = Column(String(50), nullable=False)  # minus word, plus words, ...
    position: str = Column(Integer, default=0)  # 0, when don't need execution_order
    value: str = Column(String(50), nullable=False)

    __table_args__ = (
        UniqueConstraint('client_app_ID', 'feature', name='unique_index'),
    )

    client_app = relationship("ClientApps", back_populates="filter_last")


class FilterHist(Base):
    client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'))
    feature: str = Column(String(50), nullable=False)  # minus word, plus words, ...
    position: str = Column(Integer, default=0)  # 0, when don't need execution_order
    value: str = Column(String(50), nullable=False)
    # insert_time is insert_time of ..._last table (look into a trigger)

    client_app = relationship("ClientApps", back_populates="filter_hist")


class Payments(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    client_app_ID: int = Column(Integer, ForeignKey('client_apps.id'), nullable=False)
    feature: str = Column(Enum('ticket_purchase', 'ticket_upgrade',
                               'status_purchase', 'status_upgrade', 'status_prolongation'), nullable=False)
    amount: int = Column(Integer, default=1, nullable=False)  # 1 - at least one should be bought to be in the table
    total_price: int = Column(Integer, default=0, nullable=False)  # 0 - free plan
    currency: str = Column(Enum('RUB'), default='RUB', nullable=False)
    # TODO: if 'total_price' is 0, then must be subscribed to the my groups (realise it)
    action_done: bool = Column(Boolean, default='None', nullable=False)
    note: str = Column(String(100), default='None', nullable=False)

    user = relationship("Users", back_populates="payments")
    client_app = relationship("ClientApps", back_populates="payments")
    # TODO:
    # registration = relationship("Registrations", back_populates="payment")

    __table_args__ = (
        UniqueConstraint('user_ID', 'feature', 'total_price', 'currency', 'action_done', name='unique_index'),
    )


# class Registrations(Base):
#     user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
#     # ticket_ID: int = Column(Integer, ForeignKey('tickets.id'), default='None', nullable=False)
#     # payment_ID: int = Column(Integer, ForeignKey('payments.id'), default='None', nullable=False)
#     # TODO: should I give opportunity register friends: indicate 'amounts' ?
#
#     user = relationship("Users", back_populates="registrations")
#     # ticket = relationship("Tickets", back_populates="registrations")
#     # payment = relationship("Payments", back_populates="registration")
#
#     __table_args__ = (
#         UniqueConstraint('user_ID', name='unique_index'),  # 'ticket_ID'
#     )


class Statuses(Base):
    name: str = Column(Enum('user', 'client', 'assistant', 'admin', 'root'), default='user', nullable=False)
    system_level: int = Column(Integer, default=5, nullable=False)
    period_days: int = Column(Integer, nullable=False)  # amount days, when the subscription will be active
    discount: float = Column(Float, default=0, nullable=False)  # 0 - not discount
    price: int = Column(Integer, default=0, nullable=False)  # 0 - free plan
    currency: str = Column(Enum('RUB'), default='RUB', nullable=False)
    description: str = Column(String(500), default='None', nullable=False)

    subscriptions = relationship("Subscriptions", back_populates='status')

    __table_args__ = (
        UniqueConstraint('name', 'system_level', 'period_days', 'discount', 'price', 'currency', 'description'),
    )


class Subscriptions(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    status_ID: int = Column(Integer, ForeignKey('statuses.id'), nullable=False)
    expired_date: datetime = Column(Date, nullable=False)

    user = relationship("Users", back_populates='subscriptions')
    status = relationship("Statuses", back_populates='subscriptions')


class Experience(Base):
    user_ID: int = Column(Integer, ForeignKey('users.id'), nullable=False)
    feature: str = Column(Enum('question', 'expectation', 'feedback'), nullable=False)
    value: str = Column(String(700), default='None')  # None - not value

    user = relationship("Users", back_populates="experience")

    __table_args__ = (
        UniqueConstraint('user_ID', 'feature', 'value', name='unique_index'),
    )


Base.metadata.create_all(engine)


# TODO: insert (configurate) here initial statuses to Statuses table.
# Statuses()

# create trigger function for all tables with '_last' end.
def trigger_to_hist_table(table_name_last: str, column_names: set):
    table_name_hist = table_name_last.replace('_last', '_hist')
    return text(f"""
                CREATE OR REPLACE TRIGGER {table_name_last}_to_hist_table
                BEFORE UPDATE ON {table_name_last}
                FOR EACH ROW
                BEGIN
                    INSERT INTO {table_name_hist} ({', '.join(column_names)})
                    VALUES ({', '.join(map(lambda item: 'OLD.' + item, column_names))});
                END;
                """)


with engine.connect() as connection:
    all_tables = Base.metadata.tables
    # leave only table names where '_last' ends
    tables_name_last = [name for name in all_tables if '_last' in name]

    for name in tables_name_last:
        table = all_tables[name]
        columns = {column.name for column in table.columns} - {'id'}
        # execute trigger
        connection.execute(trigger_to_hist_table(table_name_last=name, column_names=columns))

# if __name__ == '__main__':
#     Session = sessionmaker()
#     Session.configure(bind=engine)
#     Session = Session()
# #
# #
# new_user = Users(id=12345, name='Petr', birthday='1996-09-03', gender=None)
# # new_user = Users(name='Petr')
# Session.add(new_user)
# Session.commit()

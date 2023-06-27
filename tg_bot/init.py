from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.filters.callback_data import CallbackData
from aiogram.types import BotCommand, TelegramObject
from aiogram.fsm.state import StatesGroup, State
from aiogram.types.user import User as AiogramUser

from tg_bot.data_structure import users, TgData, DBUser, UserWorkflow
from tg_bot.utils.log import del_and_log_user_action


# TODO: make that block (/stop) of the bot will be written into BotInteraction
class CustomMiddleware(BaseMiddleware):
    def __init__(self, session_pool):
        super().__init__()
        self.session_pool = session_pool

    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: Dict[str, Any]
    ) -> Any:

        update_id = event.update_id
        event_type: str = [attr_name for attr_name, attr_value in vars(event).items() if attr_value is not None].pop()
        attr = getattr(event, event_type)  # of: callback_query, message, edited_message or other
        not_empty_attr_names: list = [attr_name for attr_name, attr_value in vars(attr).items() if attr_value is not None]
        tg_user: AiogramUser = attr.from_user

        async with self.session_pool() as session:
            if tg_user.id not in users:  # if an account was not added to users dict
                # create a new account into DB and have a copy on the local machine, add workflow for the user
                users[tg_user.id] = TgData(DBUser=await DBUser.create(session=session, tg_user=tg_user),
                                           UserWorkflow=UserWorkflow(tg_user.id))

            tg_user_to_db: set = {"first_name", "last_name", "username", "language_code", "is_premium"}
            await users[tg_user.id].DBUser \
                .update_account_last_info(fresh_data={name: str(getattr(tg_user, name)) for name in tg_user_to_db})
            # log user actions: datetime, update_id, event_type, message_id, user_name, data
            # TODO: fix logging_user_action -- make simpler and input into User
            is_mes_del = await del_and_log_user_action(attr, not_empty_attr_names, event_type, update_id, users, tg_user)
            if not is_mes_del:  # mes is deleted if it's not a text;
                # without the 'if' can be error (trying del twice the same message),
                # when del mes in 'del_and_log_user_action', after del the mes in 'message_delete.py' (sometimes)
                data['session'] = session  # add session to data to have ability use it in any function under handler
                await handler(event, data)


class MyCallback(CallbackData, prefix="my"):
    cb_data: str
    event_ID: int


class MyCB(CallbackData, prefix="my"):
    cb_data: str
    button_text: str
    feature: str


class MySG(StatesGroup):
    # Commands with description for a bot menu
    n_attempts_send_sms: int = None
    returned_to_sms: int = None
    is_verification_passed: bool = False

    # States of the tg bot
    main = State()
    phone = State()
    sms_code = State()
    tinder_token = State()


menu_commands: list = [
    BotCommand(command="start", description="Let's start from initial point"),
]



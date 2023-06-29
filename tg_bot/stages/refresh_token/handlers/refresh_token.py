import inspect
import os

from aiogram import Router
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, User

from tg_bot.data_structure import users
from tg_bot.init import MySG
from tg_bot.utils.keyboard_pattern import create_inline_keyboard
from tg_bot.utils.notify_support_team import notify_support_team

router = Router()
filename = os.path.basename(__file__)


def keyboard(response: dict) -> InlineKeyboardMarkup:
    status = response.get('meta', {}).get('status')
    menu = []
    if status != 200:  # if error occurs
        b1 = InlineKeyboardButton(text='send new code', callback_data='send_sms_code')
        b2 = InlineKeyboardButton(text='set another phone', callback_data='get_refresh_token')
        menu.append([b1, b2])

    # TODO: guide client if after many attempts (how many ?) code stile haven't come
    return create_inline_keyboard(menu, report=True, main_menu=True)


async def message(response: dict, response_api_token_status: int | None, user_id: int, username: str) -> str:
    status = response.get('meta', {}).get('status')

    if status == 200:  # without errors
        if not (is_new_user := response.get('data', {}).get('is_new_user')):
            if response_api_token_status == 200:
                text = f"Greate, you pass verification.\n" \
                       f"Now go to the main menu, and choose what can I do for you"
            else:
                await notify_support_team(error=True, username=username, user_id=user_id, filename=filename,
                                          error_line=inspect.currentframe().f_lineno, response=response)
                text = "Something went wrong.\n" \
                       "We have got the error and just started to fix it."
        else:
            last_phone = users[user_id].DBUser.orm_tinder_account_info.get('phone').value
            text = f"This {last_phone} phone number have never been used to sign up for Tinder.\n" \
                   f"Please, register Tinder account via the phone number or use another one.\n" \
                   f"'Menu' -> '/start'"

    else:
        code_error = response.get('error', {}).get('code')
        if status == 400:
            text = f"The code is invalid.\n" \
                   f"Enter another code."
        else:
            await notify_support_team(error=True, username=username, user_id=user_id, filename=filename,
                                      error_line=inspect.currentframe().f_lineno, response=response)
            text = "Something went wrong.\n" \
                   "We have got the error and just started to fix it."

    return text


@router.message(MySG.sms_code)
async def request_refresh_token(mes: Message) -> None:
    user: User = mes.from_user
    await users[user.id].UserWorkflow.del_keyboard()
    await users[user.id].UserWorkflow.del_useless_messages()

    # save the code and request a tinder refresh_token
    user_db = users[user.id].DBUser
    response_refresh_token = await user_db.ask_tinder_refresh_token(code=mes.text)

    status = response_refresh_token.get('meta', {}).get('status')
    is_new_user = response_refresh_token.get('data', {}).get('is_new_user')

    response_api_token_status: None = None
    if status == 200 and not is_new_user:
        response_api_token = await user_db.ask_tinder_api_token()
        response_api_token_status: int = response_api_token.get('meta', {}).get('status')

    mes_data = await mes.answer(text=await message(response_refresh_token, response_api_token_status, user.id, user.username),
                                reply_markup=keyboard(response_refresh_token),
                                parse_mode='HTML')

    users[user.id].UserWorkflow.edit_message = mes_data.message_id
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id

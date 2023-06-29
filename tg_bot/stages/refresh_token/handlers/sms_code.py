import inspect
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from tg_bot.data_structure import users, bot
from tg_bot.init import MySG
from tg_bot.utils.config import dice_id
from tg_bot.utils.keyboard_pattern import create_inline_keyboard
from tg_bot.utils.notify_support_team import notify_support_team
from tg_bot.utils.validate_data_format import del_not_digits, right_sms_code

router = Router()
filename = os.path.basename(__file__)


def keyboard(response: dict) -> InlineKeyboardMarkup:
    status = response.get('meta', {}).get('status')
    row = []
    if status == 200:
        b1 = InlineKeyboardButton(text='send new code', callback_data='send_sms_code')
        row.append(b1)
    b2 = InlineKeyboardButton(text='set another phone', callback_data='phone_ask')
    row.append(b2)
    menu = [row]
    # TODO: allow send message one in every 1 minute ???
    # TODO: guide client if after many attempts (how many ?) code stile haven't come
    return create_inline_keyboard(menu, report=True)


async def message(response: dict, phone: str, user_id: int, username: str) -> str:
    status = response.get('meta', {}).get('status')
    n_attempts = users[user_id].DBUser.received_phones.get(phone)  # amount sms attempts (sent) for the last_phone

    if status == 200:
        len_sms_code = response.get('data', {}).get('otp_length')
        users[user_id].DBUser.len_sms_code = len_sms_code
        len_sms_code = f"{len_sms_code}-" if bool(len_sms_code) else ''

        if n_attempts < 2:
            # TODO: client didn't understand is SMS or message not to phone
            # TODO: client didn't understand where sms will come
            # TODO: client didn't understand after how many time he should press 'send new code'
            #  -- make sending automatically with timer? like I will notice you when It will come
            # TODO: if customer send other phone number, the number SMS counter didn't change, just increasing
            text = f"Once you get it, write the {len_sms_code}digits to authenticate you.\n" \
                   f"After authentication you can automatically like people and send messages.\n" \
                   f"You can see the results in your Tinder account."
        else:
            text = f"Sent you {n_attempts} SMS to {phone}.\n" \
                   f"Write the {len_sms_code}digits code\n" \
                   f"from the last one to authenticate you"
    else:
        code_error = response.get('error', {}).get('code')
        text = f"Code error: {code_error}"

        if status == 429:
            await notify_support_team(error=True, username=username, user_id=user_id, filename=filename,
                                      error_line=inspect.currentframe().f_lineno, response=response)
            text += f"\nFailed rate limiter check.\n" \
                    f"Please, try again a little bit later"

        elif status == 403:
            text = f"Wrong phone number.\n" \
                   f"Please try other."

        else:
            await notify_support_team(error=True, username=username, user_id=user_id, filename=filename,
                                      error_line=inspect.currentframe().f_lineno, response=response)
            text = "Something went wrong.\n" \
                   "We have got the error and just started to fix it."

        if n_attempts > 1:
            text += f"\nAttempt {n_attempts}"
    return text


def message_error(user_id: int) -> str:
    len_sms_code = users[user_id].DBUser.len_sms_code
    len_sms_code = f"{len_sms_code}-" if bool(len_sms_code) else ''
    text = f"It looks like your inputted code format is incorrect.\n" \
           f"Try again. Write the {len_sms_code}digits code"
    return text


@router.message(MySG.phone)
async def send_sms_code(mes: Message, state: FSMContext) -> None:
    user = mes.from_user
    await users[user.id].UserWorkflow.del_useless_messages()

    phone = f'+{del_not_digits(mes.text)}'
    response: dict = await users[user.id].DBUser.add_sms_attempt(phone)
    sticker_data = await mes.answer_sticker(sticker=dice_id)  # send sticker - dice
    mes_data = await mes.answer(text=await message(response=response, phone=phone,
                                                   user_id=user.id, username=user.username),
                                reply_markup=keyboard(response=response),
                                parse_mode='HTML')

    users[user.id].UserWorkflow.add_to_delete_queue([sticker_data.message_id])
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id
    users[user.id].UserWorkflow.edit_message = mes_data.message_id  # save a message to edit it after

    # Attempt create auto message sending
    # respond = {'data': {'otp_length': 200}}  # only to start the next cycle
    # while respond.get('data', {}).get('otp_length') == 200 and not MySG.inputted_code:
    #     respond = send_to(new_phone)  # Q: should I make it asynchronous?\
    #     mes_data = await respond_wrapper(chat_id=mes.from_user.id, respond=respond, state=state)
    #     time.sleep(30)
    #     if not MySG.inputted_code:
    #         await state.set_state(MySG.sms_code)
    await state.set_state(MySG.sms_code)


@router.callback_query(F.data == "send_sms_code")
async def send_sms_code(callback: CallbackQuery, state: FSMContext) -> None:
    # TODO: make it: if a code came to a priviouse number... -> give opportunity in menu choose a phone to input a sms_code
    user = callback.from_user

    last_phone: str = users[user.id].DBUser.orm_tinder_account_info.get('phone').value
    response: dict = await users[user.id].DBUser.add_sms_attempt(last_phone)
    edit_mes_id = users[user.id].UserWorkflow.edit_message
    mes_data = await bot.edit_message_text(chat_id=user.id, message_id=edit_mes_id,
                                           text=await message(response=response, phone=last_phone,
                                                              user_id=user.id, username=user.username),
                                           reply_markup=keyboard(response), parse_mode='HTML')

    users[user.id].UserWorkflow.edit_message = mes_data.message_id
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id

    await state.set_state(MySG.sms_code)


@router.message(MySG.sms_code, lambda mes: not right_sms_code(user_id=mes.from_user.id, sms_code=mes.text))
async def check_sms_code(mes: Message) -> None:
    user = mes.from_user
    await users[user.id].UserWorkflow.del_keyboard()
    mes_data = await mes.answer(text=message_error(user.id),
                                reply_markup=keyboard(),
                                parse_mode='HTML')

    users[user.id].UserWorkflow.edit_message = mes_data.message_id
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id
    users[user.id].UserWorkflow.add_to_delete_queue([mes.message_id, mes_data.message_id])

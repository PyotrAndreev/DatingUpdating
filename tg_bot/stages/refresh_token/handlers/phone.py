from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from tg_bot.data_structure import users, bot
from tg_bot.init import MySG
from tg_bot.utils.validate_data_format import right_phone_number

router = Router()


def keyboard() -> InlineKeyboardMarkup:
    pass
    # TODO: allow sending message one in every 1 minute ???
    # TODO: guide client if after many attempts (how many ?) code stile haven't come


def message(user_id: int) -> str:
    text = f"Send your Tinder registration phone number\n"

    tinder_account_info = users[user_id].DBUser.orm_tinder_account_info
    if phone_obj := tinder_account_info.get('phone'):  # if any phone exists => attempt of changing
        phone: str = phone_obj.value
        text = f"You previously provided this phone number: {phone}\n" \
               f"If you want try with another Tinder phone number\n" \
               f"to link your Tinder profile with you, write another one.\n" \
               f"If you want try again with the same phone number,\n" \
               f"write the {phone} again.\n\n" \

    text += "Use the next format:\n" \
            "[country_code][state_code][cellphone_number]\n" \
            "example: +9 *** *******\n\n" \
            f"We will send a message to be sure that it's your account.\n\n" \
            f"Currently we do not work with Russian phone numbers."

    return text


def message_wrong_format(wrong_phone: str):
    text = f"Looks like the phone number format is incorrect.\n" \
           f"You inputted: {wrong_phone}" \
           f"Should be like: +9 *** *** ****,\n" \
           f"with '+9' as a country code example.\n" \
           f"Please send your phone again using the correct format:\n" \
           f"[country_code][state_code][cellphone_number]\n\n" \
           f"Currently we do not work with Russian phone numbers."
    return text


@router.callback_query(F.data == "phone_ask")
async def ask_phone(callback: CallbackQuery, state: FSMContext) -> None:
    user = callback.from_user
    edit_mes_id = users[user.id].UserWorkflow.edit_message

    await bot.edit_message_text(chat_id=user.id,
                                message_id=edit_mes_id,
                                text=message(user.id),
                                parse_mode='HTML')
    await state.set_state(MySG.phone)


@router.message(MySG.phone, lambda mes: not right_phone_number(mes.text))
async def check_phone(mes: Message) -> None:
    mes_data = await mes.answer(text=message_wrong_format(wrong_phone=mes.text),
                                parse_mode='HTML')
    users[mes.from_user.id].UserWorkflow.add_to_delete_queue([mes_data.message_id, mes.message_id])

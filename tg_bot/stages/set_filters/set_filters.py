from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

from tg_bot.data_structure import DBUser
from tg_bot.data_structure import users, bot
from tg_bot.utils.keyboard_pattern import create_inline_keyboard

router = Router()


# def keyboard(user_id: int) -> InlineKeyboardMarkup:
#     is_report = True
#     user: DBUser = users[user_id].DBUser
#
#     if 'refresh_token' not in user.orm_tg_account_info:
#         b1 = InlineKeyboardButton(text='connect with your Tinder account', callback_data='phone_ask')
#         menu = [[b1]]
#     else:
#         b1 = InlineKeyboardButton(text='set message template', callback_data='')
#         b2 = InlineKeyboardButton(text='set filters', callback_data='')
#         b3 = InlineKeyboardButton(text='run auto searching', callback_data='')
#         menu = [[b1, b2], [b3]]
#
#     if user.orm_user.system_level >= 20:  # >= assistant_admin (config.py)
#         is_report = False
#         b4 = InlineKeyboardButton(text='admin menu', callback_data='administration')
#         menu.append([b4])
#
#     return create_inline_keyboard(menu, report=is_report)


def message() -> str:
    text = f"Coming soon"
    return text


@router.callback_query(F.data == "set_filters")
async def start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()  # drop state
    user: User = callback.from_user
    await users[user.id].UserWorkflow.del_useless_messages()

    # if mes_id := users[user.id].UserWorkflow.edit_message:
    mes_data = await callback.answer(text=message(),
                                     parse_mode='HTML')
    # else:
    #     await users[user.id].UserWorkflow.del_keyboard()
    #     mes_data = await callback.message.answer(text=message(user.first_name),
    #                                              parse_mode='HTML',
    #                                              reply_markup=keyboard(user.id))
    #
    # users[user.id].UserWorkflow.edit_message = mes_data.message_id

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

from tg_bot.data_structure import DBUser
from tg_bot.data_structure import users, bot
from tg_bot.utils.keyboard_pattern import create_inline_keyboard

router = Router()


def keyboard(user_id: int) -> InlineKeyboardMarkup:
    is_report = True
    user: DBUser = users[user_id].DBUser
    print(f"user.orm_tinder_account_info.get('refresh_token'): {user.orm_tinder_account_info.get('refresh_token')}")
    if not user.orm_tinder_account_info.get('refresh_token'):
        b1 = InlineKeyboardButton(text='connect with your Tinder account', callback_data='phone_ask')
        menu = [[b1]]
    else:
        b1 = InlineKeyboardButton(text='message template', callback_data='message_template')
        b2 = InlineKeyboardButton(text='filters', callback_data='set_filters')
        b3 = InlineKeyboardButton(text='auto searching', callback_data='pass')
        b4 = InlineKeyboardButton(text='statistic', callback_data='pass')
        menu = [[b1, b2], [b3, b4]]

    if user.orm_user.system_level >= 20:  # >= assistant_admin (config.py)
        is_report = False
        b4 = InlineKeyboardButton(text='admin', callback_data='administration')
        menu.append([b4])

    return create_inline_keyboard(menu, report=is_report)


def message(first_name: str) -> str:
    text = f"Hi, {first_name}!\n" \
           f"Let's boost your Tinder attractiveness.\n" \
           f"You should have Tinder account for the first."
    return text


@router.message(Command('start'))
async def start(mes: Message) -> None:
    await mes.delete()  # del the '/start' message
    user: User = mes.from_user
    mes_data = await mes.answer(text=message(user.first_name),
                                parse_mode='HTML',
                                reply_markup=keyboard(user.id))
    users[user.id].UserWorkflow.edit_message = mes_data.message_id


@router.callback_query(F.data == "start")
async def start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()  # drop state
    user: User = callback.from_user
    await users[user.id].UserWorkflow.del_useless_messages()

    if mes_id := users[user.id].UserWorkflow.edit_message:
        mes_data = await bot.edit_message_text(chat_id=user.id,
                                               message_id=mes_id,
                                               text=message(user.first_name),
                                               parse_mode='HTML',
                                               reply_markup=keyboard(user.id))
    else:
        await users[user.id].UserWorkflow.del_keyboard()
        mes_data = await callback.message.answer(text=message(user.first_name),
                                                 parse_mode='HTML',
                                                 reply_markup=keyboard(user.id))

    users[user.id].UserWorkflow.edit_message = mes_data.message_id

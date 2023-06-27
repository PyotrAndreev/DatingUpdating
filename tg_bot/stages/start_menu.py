from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

from tg_bot.utils.bot_workflow import create_inline_keyboard
from tg_bot.utils.data_structure import users, bot

router = Router()


# def is_admin(user_id: int) -> bool:
#     admin_flag = False
#     if user_id in [266152771, 881321294]:  # TODO: is_admin - receive from DB.  Make root user.
#         admin_flag = True
#     return admin_flag


def keyboard(user_id: int) -> InlineKeyboardMarkup:
    print(f'users: {users}')
    print(f'user_id: {user_id}')
    if 'refresh_token' not in users[user_id].TgUser.orm_tg_account_info:
        b1 = InlineKeyboardButton(text='connect with your Tinder account', callback_data='phone_ask')
        menu = [[b1]]
    else:
        b1 = InlineKeyboardButton(text='set message template', callback_data='')
        b2 = InlineKeyboardButton(text='set filters', callback_data='')
        b3 = InlineKeyboardButton(text='run auto searching', callback_data='')
        menu = [[b1, b2], [b3]]

    # if is_admin(user_id):
    #     b3 = InlineKeyboardButton(text='admin menu', callback_data='administration')
    #     menu.append([b3])

    return create_inline_keyboard(menu, report=True)


def message(first_name: str, user_id: int) -> str:
    text = f"Hi, <b>{first_name}</b>!\n" \
           f"Let's boost your Tinder attractiveness." \
           f"\nYou should have Tinder account for the first."

    # if is_admin(user_id):
    #     text += "\n\nYour are admin."
    return text


@router.message(Command('start'))
async def start(mes: Message) -> None:
    await mes.delete()  # del the '/start' message
    user: User = mes.from_user
    mes_data = await mes.answer(text=message(user.first_name, user.id),
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
                                               text=message(user.first_name, user.id),
                                               parse_mode='HTML',
                                               reply_markup=keyboard(user.id))
    else:
        await users[user.id].UserWorkflow.del_keyboard()
        mes_data = await callback.message.answer(text=message(user.first_name, user.id),
                                                 parse_mode='HTML',
                                                 reply_markup=keyboard(user.id))

    users[user.id].UserWorkflow.edit_message = mes_data.message_id

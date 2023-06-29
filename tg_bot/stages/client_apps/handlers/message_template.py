from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

from tg_bot.data_structure import DBUser
from tg_bot.data_structure import users, bot
from tg_bot.init import MySG
from tg_bot.utils.keyboard_pattern import create_inline_keyboard

router = Router()


def keyboard(stage: str = None) -> InlineKeyboardMarkup:
    menu = []
    if stage == 'print':
        b1 = InlineKeyboardButton(text='set new template', callback_data='message_template')
        menu.append([b1])
    return create_inline_keyboard(menu, report=True, main_menu=True)


def message(stage: str) -> str:
    if stage == 'set':
        text = f"Write here a message template what will be send automatically as the first message to everyone, \n" \
               f"when you will run auto liker and have a match. \n\n" \
               f"If you want use a name of pearson to whom you write,\n" \
               f"then use '[name]' instead of a pearson name.\n" \
               f"'[name]' <u>must be</u> with '[' and ']'!\n\n" \
               f"Example:\n 'Hey [name], how are you doing?'"
    elif stage == 'print':
        text = f"Your template have been saved.\n" \
               f"If it is correct, then go to 'main menu' and run auto liker."
    return text


@router.callback_query(F.data == "message_template")
async def ask_message_template(callback: CallbackQuery, state: FSMContext) -> None:
    user: User = callback.from_user

    mes_id = users[user.id].UserWorkflow.edit_message
    mes_data = await bot.edit_message_text(chat_id=user.id,
                                           message_id=mes_id,
                                           text=message(stage='set'),
                                           parse_mode='HTML',
                                           reply_markup=keyboard())

    users[user.id].UserWorkflow.edit_message = mes_data.message_id
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id
    await state.set_state(MySG.message_template)


@router.message(MySG.message_template)
async def request_refresh_token(mes: Message) -> None:
    user: User = mes.from_user
    await users[user.id].UserWorkflow.del_keyboard()
    await users[user.id].DBUser.save_message_template(mes.text)

    mes_data = await mes.answer(text=message(stage='print'),
                                parse_mode='HTML',
                                reply_markup=keyboard(stage='print'))
    users[user.id].UserWorkflow.edit_message = mes_data.message_id

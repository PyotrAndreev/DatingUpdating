from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, User

from tg_bot.data_structure import users, bot
from tg_bot.init import MyCB, MySG
from tg_bot.utils.keyboard_pattern import create_inline_keyboard

router = Router()


def keyboard(the_end: bool = None) -> InlineKeyboardMarkup:
    menu = []
    if not the_end:
        callback = 'report'
        b1 = InlineKeyboardButton(text='error', callback_data=MyCB(cb_data=callback, button_text='error',
                                                                   feature='report_type').pack())
        b2 = InlineKeyboardButton(text='improvement suggestion', callback_data=MyCB(cb_data=callback,
                                                                                    button_text='improvement suggestion',
                                                                                    feature='report_type').pack())
        b3 = InlineKeyboardButton(text='cooperation proposal', callback_data=MyCB(cb_data=callback,
                                                                                  button_text='cooperation proposal',
                                                                                  feature='report_type').pack())
        b4 = InlineKeyboardButton(text='another', callback_data=MyCB(cb_data=callback,
                                                                     button_text='another',
                                                                     feature='report_type').pack())

        menu = [[b1, b2], [b3, b4]]
    return create_inline_keyboard(menu, main_menu=True)


def message(report_type: str = None, the_end: bool = None) -> str:
    text: str = f"Select a message type you would like to send us."

    if report_type:
        if report_type == "error":
            text: str = f"Describe the error you noticed in our service.\n" \
                        f"How did you come to her?"

        elif report_type == "improvement suggestion":
            text: str = f'We are always ready to make the service more convenient and easier for you to use.\n' \
                        f'Write your suggestions for improving the service:'

        elif report_type == "cooperation proposal":
            text: str = f'We are open to cooperation.\n' \
                        f'Describe your offer:'

        elif report_type == "another":
            text: str = f'We would love to read your comments:'

    elif the_end:
        text: str = f"The report have been sent.\n" \
                    f"Rest assured, we will read that. Thank you."

    return text

# TODO: after the step (report) the state and other parameters should be the same as before 'contact us' and return on the same bot step


@router.callback_query(F.data == "report_type")
async def report_type(callback: CallbackQuery, state: FSMContext) -> None:
    # TODO: make the function universe, that at the end it will return to the previous step
    # TODO: save current state to return it of the end of 'report.py'
    # await state.clear()  # drop state
    user: User = callback.from_user
    await users[user.id].UserWorkflow.del_useless_messages()

    text = message()
    parse_mode = 'HTML'
    inkb = keyboard()
    if mes_id := users[user.id].UserWorkflow.edit_message:
        mes_data = await bot.edit_message_text(chat_id=user.id,
                                               message_id=mes_id,
                                               text=text,
                                               parse_mode=parse_mode,
                                               reply_markup=inkb)
    else:
        await users[user.id].UserWorkflow.del_keyboard()
        mes_data = await callback.message.answer(text=text,
                                                 parse_mode=parse_mode,
                                                 reply_markup=inkb)

    users[user.id].UserWorkflow.edit_message = mes_data.message_id


@router.callback_query(MyCB.filter(F.cb_data == "report"))
async def take_report(callback: CallbackQuery, callback_data: MyCB, state: FSMContext) -> None:
    user: User = callback.from_user
    users[user.id].DBUser.report_type = callback_data.button_text

    mes_id = users[user.id].UserWorkflow.edit_message
    mes_data = await bot.edit_message_text(chat_id=user.id,
                                           message_id=mes_id,
                                           text=message(report_type=callback_data.button_text),
                                           parse_mode='HTML')
    await state.set_state(MySG.save_report)


@router.message(MySG.save_report)
async def save_report(mes: Message) -> None:
    user: User = mes.from_user
    # await users[user.id].UserWorkflow.del_keyboard()

    await users[user.id].DBUser.send_report(text=mes.text, tg_user=user)
    mes_data = await mes.answer(text=message(the_end=True),
                                parse_mode='HTML',
                                reply_markup=keyboard(the_end=True))
    users[user.id].UserWorkflow.useless_keyboard = mes_data.message_id
    users[user.id].UserWorkflow.edit_message = None  # to not edit any message: TODO: make more univers and pleasant

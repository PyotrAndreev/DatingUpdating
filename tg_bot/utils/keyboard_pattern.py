import asyncio

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from tg_bot.data_structure import bot


def create_inline_keyboard(menu: list[None, list[InlineKeyboardButton]] = [],
                           main_menu: bool = True, report: bool = True) -> InlineKeyboardMarkup:
    """menu: list of menu rows"""
    last_row = []

    if report:
        report: InlineKeyboardButton = InlineKeyboardButton(text='Сообщить о / предложить', callback_data='report_type')
        last_row.append(report)

    if main_menu:
        main_menu: InlineKeyboardButton = InlineKeyboardButton(text='Главное меню', callback_data='start')
        last_row.append(main_menu)

    menu.append(last_row)
    return InlineKeyboardMarkup(inline_keyboard=menu)


def keyboard() -> InlineKeyboardMarkup:
    b1 = InlineKeyboardButton(text='Отчество не нужно', callback_data='speaker_tg_username')
    menu = [[b1]]
    return create_inline_keyboard(menu, main_menu=False)


async def ask_patronymic(mes: Message) -> None:
    mes_data = await bot.send_message(chat_id=266152771,
                                      text='test',
                                      parse_mode='HTML',
                                      reply_markup=keyboard())


if __name__ == '__main__':
    asyncio.run(ask_patronymic(mes='test'))

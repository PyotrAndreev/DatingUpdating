from aiogram import Router
from aiogram.types import Message

from tg_bot.data_structure import bot

router = Router()


@router.message()
async def del_user_message(mes: Message) -> None:
    print(f'mes: {mes}')
    await mes.delete()
    await bot.delete_webhook()


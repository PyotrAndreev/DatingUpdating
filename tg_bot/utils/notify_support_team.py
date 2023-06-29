import os

from aiogram import Bot

from tg_bot.utils.config import support_team

# TODO: leave only one bot (in one file); if inside 'dara_structure.py', then recursive links exist
bot = Bot(token=os.environ.get('tgbotToken'))


async def notify_support_team(text: str = None, report=False, report_type: str = None,
                              error=False, username: str = None, user_id: int = None,
                              filename: str = None, error_line: int = None, response: dict = None) -> None:

    for tg_id in support_team:
        if error:
            text = f"<b><u>Error</u></b>:\n" \
                   f"client = @{username}\n" \
                   f"account_tg_user_id = {user_id}\n" \
                   f"file = {filename}: {error_line}\n\n" \
                   f"<u>response</u>:\n" \
                   f"{response}"

        elif report:
            text = f"<b><u>Report</u></b>:\n" \
                   f"type = {report_type}\n" \
                   f"client = @{username}\n" \
                   f"account_tg_user_id = {user_id}\n\n" \
                   f"{text}"

        await bot.send_message(chat_id=tg_id,
                               text=text,
                               parse_mode='HTML')

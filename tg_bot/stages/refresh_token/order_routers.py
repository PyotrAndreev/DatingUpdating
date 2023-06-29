from tg_bot.stages.refresh_token.handlers.phone import router as phone
from tg_bot.stages.refresh_token.handlers.sms_code import router as sms_code
from tg_bot.stages.refresh_token.handlers.refresh_token import router as refresh_token

refresh_token = [phone,
                 sms_code,
                 refresh_token]

from tg_bot.stages.client_apps.handlers.message_template import router as message_template
from tg_bot.stages.refresh_token.handlers.sms_code import router as sms_code
from tg_bot.stages.refresh_token.handlers.refresh_token import router as refresh_token

client_apps = [message_template]

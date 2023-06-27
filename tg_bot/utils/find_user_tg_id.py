import os
import asyncio
from pyrogram import Client
from pyrogram.raw.base.contacts import ResolvedPeer
from pyrogram.raw.functions.contacts import ResolvePhone

from dotenv import load_dotenv
from pyrogram.types import User

# Load environment variables from .env file
load_dotenv()

api_id = os.environ.get('api_id')
api_hash = os.environ.get('api_hash')

# TODO: how can I use the same session? How can I use 'my_account.session'? How can I register people automatically?

async def find_tg_id(**identifier) -> int:
    """params: user_ids, phone"""
    """username: can be a phone, if the contact in your Telegram address book"""
    async with Client("my_account", api_id, api_hash) as app:
        # await app.send_message(username, "Greetings from **Pyrogram**!")
        # if 'phone' in identifier:  # if the account has not interacted with the user before
        #     data: ResolvedPeer = await app.invoke(ResolvePhone(**identifier))
        #     user: User = data.users[0]
        # else:
        try:
            await app.get_contacts()  # refresh contacts
            user: User = await app.get_users(**identifier)
            user_id: int = user.id
            return user_id
        except:
            return False


if __name__ == '__main__':
    print(asyncio.run(find_tg_id(user_ids="artemborin")))

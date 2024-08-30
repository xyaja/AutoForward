import asyncio
import logging
import logging.config
from database import db
from config import Config
from pyrogram import Client, __version__
from pyrogram.raw.all import layer
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
import traceback

logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)

class Bot(Client):
    def __init__(self):
        super().__init__(
            Config.BOT_SESSION,
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=50
        )
        self.log = logging

    async def start(self):
        await super().start()
        me = await self.get_me()
        self.log.info(f"{me.first_name} with Pyrogram v{__version__} (Layer {layer}) started on @{me.username}.")
        self.id = me.id
        self.username = me.username
        self.first_name = me.first_name
        self.set_parse_mode(ParseMode.DEFAULT)
        
        text = "**๏[-ิ_•ิ]๏ Bot restarted!**"
        self.log.info(text)
        
        success = failed = 0
        users = await db.get_all_frwd()
        
        for user in users:
            chat_id = user['user_id']
            try:
                await self.send_message(chat_id, text)
                success += 1
            except FloodWait as e:
                self.log.warning(f"FloodWait: Sleeping for {e.value} seconds.")
                await asyncio.sleep(e.value + 1)
                try:
                    await self.send_message(chat_id, text)
                    success += 1
                except Exception as ex:
                    self.log.error(f"Failed to resend message to {chat_id}: {ex}")
                    failed += 1
            except Exception as ex:
                self.log.error(f"Failed to send message to {chat_id}: {ex}")
                failed += 1
        
        if (success + failed) > 0:
            await db.rmve_frwd(all=True)
            self.log.info(f"Restart message status - Success: {success}, Failed: {failed}")

    async def stop(self, *args):
        msg = f"@{self.username} stopped. Bye."
        await super().stop()
        self.log.info(msg)

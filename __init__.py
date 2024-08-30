from pyrogram import Client
from telethon.sync import TelegramClient
from decouple import config
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.DEBUG,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logging.getLogger("pyrogram").setLevel(logging.WARNING)
logging.getLogger("telethon").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

# Load environment variables
API_ID = config("API_ID", default=None, cast=int)
API_HASH = config("API_HASH", default=None)
BOT_TOKEN = config("BOT_TOKEN", default=None)
SESSION = config("SESSION", default=None)
FORCESUB = config("FORCESUB", default=None)
AUTH = config("AUTH", default=None)

# Process SUDO_USERS
SUDO_USERS = set()
if AUTH:
    SUDO_USERS = {int(auth_id) for auth_id in AUTH.split()}

# Initialize Telegram clients
try:
    bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)
except Exception as e:
    logger.error(f"Failed to start Telethon bot client: {e}")
    sys.exit(1)

try:
    userbot = Client("myacc", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)
    userbot.start()
except Exception as e:
    logger.error(f"Failed to start Pyrogram userbot client: {e}")
    logger.info("Your session expired. Please re-add it. Thanks @dev_gagan.")
    sys.exit(1)

try:
    Bot = Client(
        "SaveRestricted",
        bot_token=BOT_TOKEN,
        api_id=API_ID,
        api_hash=API_HASH
    )
    Bot.start()
except Exception as e:
    logger.error(f"Failed to start Pyrogram bot client: {e}")
    sys.exit(1)

# Your bot is now ready to be used
logger.info("All clients started successfully.")

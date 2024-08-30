import motor.motor_asyncio
from pymongo import MongoClient
from config import Config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def mongodb_version():
    """Get the MongoDB server version."""
    async with motor.motor_asyncio.AsyncIOMotorClient(Config.DATABASE_URI) as client:
        mongodb_version = client.server_info()['version']
    return mongodb_version

class Database:
    def __init__(self, uri, database_name):
        """Initialize the Database class with MongoDB connection and collections."""
        self._client = motor.motor_asyncio.AsyncIOMotorClient(uri)
        self.db = self._client[database_name]
        self.bot = self.db.bots
        self.col = self.db.users
        self.nfy = self.db.notify
        self.chl = self.db.channels

    def new_user(self, id, name):
        """Create a new user dictionary."""
        return {
            'id': id,
            'name': name,
            'ban_status': {
                'is_banned': False,
                'ban_reason': "",
            },
        }

    async def add_user(self, id, name):
        """Add a new user to the users collection."""
        user = self.new_user(id, name)
        await self.col.insert_one(user)

    async def is_user_exist(self, id):
        """Check if a user exists in the users collection."""
        user = await self.col.find_one({'id': int(id)})
        return bool(user)

    async def total_users_bots_count(self):
        """Get the total number of users and bots."""
        bcount = await self.bot.count_documents({})
        count = await self.col.count_documents({})
        return count, bcount

    async def total_channels(self):
        """Get the total number of channels."""
        count = await self.chl.count_documents({})
        return count

    async def remove_ban(self, id):
        """Remove the ban status of a user."""
        ban_status = {'is_banned': False, 'ban_reason': ''}
        await self.col.update_one({'id': id}, {'$set': {'ban_status': ban_status}})

    async def ban_user(self, user_id, ban_reason="No Reason"):
        """Ban a user with a given reason."""
        ban_status = {'is_banned': True, 'ban_reason': ban_reason}
        await self.col.update_one({'id': user_id}, {'$set': {'ban_status': ban_status}})

    async def get_ban_status(self, id):
        """Get the ban status of a user."""
        default = {'is_banned': False, 'ban_reason': ''}
        user = await self.col.find_one({'id': int(id)})
        return user.get('ban_status', default) if user else default

    async def get_all_users(self):
        """Get a list of all users."""
        return self.col.find({})

    async def delete_user(self, user_id):
        """Delete a user from the users collection."""
        await self.col.delete_many({'id': int(user_id)})

    async def get_banned(self):
        """Get a list of banned user IDs."""
        users = self.col.find({'ban_status.is_banned': True})
        b_users = [user['id'] async for user in users]
        return b_users

    async def update_configs(self, id, configs):
        """Update the configuration for a user."""
        await self.col.update_one({'id': int(id)}, {'$set': {'configs': configs}})

    async def get_configs(self, id):
        """Get the configuration for a user."""
        default = {
            'caption': None,
            'duplicate': True,
            'forward_tag': False,
            'file_size': 0,
            'size_limit': None,
            'extension': None,
            'keywords': None,
            'protect': None,
            'button': None,
            'db_uri': None,
            'filters': {
                'poll': True,
                'text': True,
                'audio': True,
                'voice': True,
                'video': True,
                'photo': True,
                'document': True,
                'animation': True,
                'sticker': True
            }
        }
        user = await self.col.find_one({'id': int(id)})
        return user.get('configs', default) if user else default

    async def add_bot(self, datas):
        """Add a bot to the bots collection."""
        if not await self.is_bot_exist(datas['user_id']):
            await self.bot.insert_one(datas)

    async def remove_bot(self, user_id):
        """Remove a bot from the bots collection."""
        await self.bot.delete_many({'user_id': int(user_id)})

    async def get_bot(self, user_id: int):
        """Get bot details by user ID."""
        return await self.bot.find_one({'user_id': user_id})

    async def is_bot_exist(self, user_id):
        """Check if a bot exists in the bots collection."""
        return bool(await self.bot.find_one({'user_id': user_id}))

    async def in_channel(self, user_id: int, chat_id: int) -> bool:
        """Check if a user is in a specific channel."""
        return bool(await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)}))

    async def add_channel(self, user_id: int, chat_id: int, title, username):
        """Add a channel to the channels collection."""
        if not await self.in_channel(user_id, chat_id):
            return await self.chl.insert_one({"user_id": user_id, "chat_id": chat_id, "title": title, "username": username})
        return False

    async def remove_channel(self, user_id: int, chat_id: int):
        """Remove a channel from the channels collection."""
        if await self.in_channel(user_id, chat_id):
            return await self.chl.delete_many({"user_id": int(user_id), "chat_id": int(chat_id)})
        return False

    async def get_channel_details(self, user_id: int, chat_id: int):
        """Get details of a specific channel."""
        return await self.chl.find_one({"user_id": int(user_id), "chat_id": int(chat_id)})

    async def get_user_channels(self, user_id: int):
        """Get all channels for a specific user."""
        channels = self.chl.find({"user_id": int(user_id)})
        return [channel async for channel in channels]

    async def get_filters(self, user_id):
        """Get the filters for a user."""
        filters = []
        filter_config = (await self.get_configs(user_id))['filters']
        for k, v in filter_config.items():
            if not v:
                filters.append(str(k))
        return filters

    async def add_frwd(self, user_id):
        """Add a user to the forward notifications collection."""
        return await self.nfy.insert_one({'user_id': int(user_id)})

    async def rmve_frwd(self, user_id=0, all=False):
        """Remove a user from the forward notifications collection."""
        query = {} if all else {'user_id': int(user_id)}
        return await self.nfy.delete_many(query)

    async def get_all_frwd(self):
        """Get a list of all users in the forward notifications collection."""
        return self.nfy.find({})

# Initialize the database connection
db = Database(Config.DATABASE_URI, Config.DATABASE_NAME)

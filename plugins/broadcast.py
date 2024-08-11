# Jishu Developer 
# Don't Remove Credit 🥺
# Telegram Channel @Madflix_Bots
# Backup Channel @JishuBotz
# Developer @JishuDeveloper




import asyncio 
import time, datetime 
from database import db 
from config import Config
from pyrogram import Client, filters 
from pyrogram.errors import InputUserDeactivated, FloodWait, UserIsBlocked
from motor.motor_asyncio import AsyncIOMotorClient as MongoClient

    @app.on_message(
        filters.command("stats") & filters.user(BOT_OWNER_ID)
    )
    async def stats_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        served_users = len(await mongo.get_served_users())
        blocked = await mongo.get_banned_count()
        text = f""" **ChatBot Stats:**
        
**Python Version :** {pyver.split()[0]}
**Pyrogram Version :** {pyrover}

**Served Users:** {served_users} 
**Blocked Users:** {blocked}"""
        await message.reply_text(text)

    @app.on_message(
        filters.command("broadcast") & filters.user(BOT_OWNER_ID)
    )
    async def broadcast_func(_, message: Message):
        if db is None:
            return await message.reply_text(
                "MONGO_DB_URI var not defined. Please define it first"
            )
        if message.reply_to_message:
            x = message.reply_to_message.message_id
            y = message.chat.id
        else:
            if len(message.command) < 2:
                return await message.reply_text(
                    "**Usage**:\n/broadcast [MESSAGE] or [Reply to a Message]"
                )
            query = message.text.split(None, 1)[1]

        susr = 0
        served_users = []
        susers = await mongo.get_served_users()
        for user in susers:
            served_users.append(int(user["user_id"]))
        for i in served_users:
            try:
                await app.forward_messages(
                    i, y, x
                ) if message.reply_to_message else await app.send_message(
                    i, text=query
                )
                susr += 1
            except FloodWait as e:
                flood_time = int(e.x)
                if flood_time > 200:
                    continue
                await asyncio.sleep(flood_time)
            except Exception:
                pass
        try:
            await message.reply_text(
                f"**Broadcasted Message to {susr} Users.**"
            )
        except:
            pass

    @app.on_message(filters.private & ~filters.edited)
    async def incoming_private(_, message):
        user_id = message.from_user.id
        if await mongo.is_banned_user(user_id):
            return
        if user_id in SUDO_USERS:
            if message.reply_to_message:
                if (
                    message.text == "/unblock"
                    or message.text == "/block"
                    or message.text == "/broadcast"
                ):
                    return
                if not message.reply_to_message.forward_sender_name:
                    return await message.reply_text(
                        "Please reply to forwarded messages only."
                    )
                replied_id = message.reply_to_message_id
                try:
                    replied_user_id = save[replied_id]
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Failed to fetch user. You might've restarted bot or some error happened. Please check logs"
                    )
                try:
                    return await app.copy_message(
                        replied_user_id,
                        message.chat.id,
                        message.message_id,
                    )
                except Exception as e:
                    print(e)
                    return await message.reply_text(
                        "Failed to send the message, User might have blocked the bot or something wrong happened. Please check logs"
                    )
        else:
            if await mongo.is_group():
                try:
                    forwarded = await app.forward_messages(
                        config.LOG_GROUP_ID,
                        message.chat.id,
                        message.message_id,
                    )
                    save[forwarded.message_id] = user_id
                except:
                    pass
            else:
                for user in SUDO_USERS:
                    try:
                        forwarded = await app.forward_messages(
                            user, message.chat.id, message.message_id
                        )
                        save[forwarded.message_id] = user_id
                    except:
                        pass

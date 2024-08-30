import asyncio
import time
import datetime
from database import db
from config import Config
from pyrogram import Client, filters
from pyrogram.errors import InputUserDeactivated, FloodWait, UserIsBlocked
from pyrogram.types import Message

@Client.on_message(filters.command(["broadcast", "b"]) & filters.user(Config.OWNER_ID) & filters.reply)
async def broadcast(bot: Client, message: Message):
    users = await db.get_all_users()
    b_msg = message.reply_to_message
    sts = await message.reply_text(
        text='Broadcasting Your Messages...'
    )
    start_time = time.time()
    total_users, _ = await db.total_users_bots_count()
    done = 0
    blocked = 0
    deleted = 0
    failed = 0
    success = 0

    for user in users:
        pti, sh = await broadcast_messages(int(user['id']), b_msg, bot.log)
        if pti:
            success += 1
            await asyncio.sleep(2)  # Adjust delay as needed
        else:
            if sh == "Blocked":
                blocked += 1
            elif sh == "Deleted":
                deleted += 1
            elif sh == "Error":
                failed += 1
        done += 1
        if done % 20 == 0:
            await sts.edit(f"<b><u>Broadcast In Progress :</u></b>\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}", parse_mode="HTML")

    time_taken = datetime.timedelta(seconds=int(time.time() - start_time))
    await sts.edit(f"<b><u>Broadcast Completed :</u></b>\n\nCompleted in {time_taken} seconds.\n\nTotal Users: {total_users}\nCompleted: {done} / {total_users}\nSuccess: {success}\nBlocked: {blocked}\nDeleted: {deleted}", parse_mode="HTML")

async def broadcast_messages(user_id: int, message: Message, log):
    try:
        await message.copy(chat_id=user_id)
        return True, "Success"
    except FloodWait as e:
        await asyncio.sleep(e.x)
        return await broadcast_messages(user_id, message, log)
    except InputUserDeactivated:
        await db.delete_user(user_id)
        log.info(f"{user_id} - Removed from Database, since deleted account.")
        return False, "Deleted"
    except UserIsBlocked:
        log.info(f"{user_id} - Blocked the bot.")
        return False, "Blocked"
    except Exception as e:
        log.error(f"Error broadcasting to {user_id}: {e}")
        return False, "Error"

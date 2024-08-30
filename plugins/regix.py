import os
import sys
import math
import time
import asyncio
import logging
from database import db
from config import Config, temp
from translation import Translation
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, MessageNotModified, RPCError
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
TEXT = Translation.TEXT

@Client.on_callback_query(filters.regex(r'^start_public'))
async def pub_(bot: Client, message: CallbackQuery):
    user = message.from_user.id
    temp.CANCEL[user] = False
    frwd_id = message.data.split("_")[2]
    
    if temp.lock.get(user) and str(temp.lock.get(user)) == "True":
        return await message.answer("Please wait until the previous task is complete", show_alert=True)
    
    sts = STS(frwd_id)
    if not sts.verify():
        await message.answer("You're clicking on my old button", show_alert=True)
        return await message.message.delete()
    
    i = sts.get(full=True)
    if i.TO in temp.IS_FRWD_CHAT:
        return await message.answer("In the target chat, a task is progressing. Please wait until the task is complete", show_alert=True)
    
    m = await msg_edit(message.message, "<code>Verifying your data, please wait.</code>")
    _bot, caption, forward_tag, data, protect, button = await sts.get_data(user)
    
    if not _bot:
        return await msg_edit(m, "<code>You didn't add any bot. Please add a bot using /settings!</code>", wait=True)
    
    try:
        client = await start_clone_bot(CLIENT.client(_bot))
    except Exception as e:
        return await m.edit(e)
    
    await msg_edit(m, "<code>Processing..</code>")
    
    try:
        await client.get_messages(sts.get("FROM"), sts.get("limit"))
    except:
        await msg_edit(m, f"**Source chat may be a private channel/group. Use a userbot (user must be a member) or make your [Bot](t.me/{_bot['username']}) an admin**", retry_btn(frwd_id), True)
        return await stop(client, user)
    
    try:
        k = await client.send_message(i.TO, "Testing")
        await k.delete()
    except:
        await msg_edit(m, f"**Please make your [UserBot/Bot](t.me/{_bot['username']}) admin in the target channel with full permissions**", retry_btn(frwd_id), True)
        return await stop(client, user)
    
    temp.forwardings += 1
    await db.add_frwd(user)
    await send(client, user, "<b>Forwarding started <a href=https://t.me/dev_gagan>Dev Gagan</a></b>")
    sts.add(time=True)
    
    sleep = 1 if _bot['is_bot'] else 10
    await msg_edit(m, "<code>Processing...</code>")
    temp.IS_FRWD_CHAT.append(i.TO)
    temp.lock[user] = locked = True
    
    if locked:
        try:
            MSG = []
            pling = 0
            await edit(m, 'Progressing', 10, sts)
            print(f"Starting Forwarding Process... From: {sts.get('FROM')} To: {sts.get('TO')} Total: {sts.get('limit')} stats: {sts.get('skip')})")
            
            async for message in client.iter_messages(
                chat_id=sts.get('FROM'),
                limit=int(sts.get('limit')),
                offset=int(sts.get('skip')) if sts.get('skip') else 0
            ):
                if await is_cancelled(client, user, m, sts):
                    return
                
                if pling % 20 == 0:
                    await edit(m, 'Progressing', 10, sts)
                
                pling += 1
                sts.add('fetched')
                
                if message == "DUPLICATE":
                    sts.add('duplicate')
                    continue
                elif message == "FILTERED":
                    sts.add('filtered')
                    continue
                
                if message.empty or message.service:
                    sts.add('deleted')
                    continue
                
                if forward_tag:
                    MSG.append(message.id)
                    notcompleted = len(MSG)
                    completed = sts.get('total') - sts.get('fetched')
                    
                    if notcompleted >= 100 or completed <= 100:
                        await forward(client, MSG, m, sts, protect)
                        sts.add('total_files', notcompleted)
                        await asyncio.sleep(10)
                        MSG = []
                else:
                    new_caption = custom_caption(message, caption)
                    details = {"msg_id": message.id, "media": media(message), "caption": new_caption, 'button': button, "protect": protect}
                    await copy(client, details, m, sts)
                    sts.add('total_files')
                    await asyncio.sleep(sleep)
        
        except Exception as e:
            await msg_edit(m, f'<b>ERROR:</b>\n<code>{e}</code>', wait=True)
            temp.IS_FRWD_CHAT.remove(sts.TO)
            return await stop(client, user)
        
        temp.IS_FRWD_CHAT.remove(sts.TO)
        await send(client, user, "<b>🎉 Forwarding completed 🥀 <a href=https://t.me/dev_gagan>SUPPORT</a>🥀</b>")
        await edit(m, 'Completed', "completed", sts)
        await stop(client, user)

async def copy(bot: Client, msg: dict, m: Message, sts: STS):
    try:
        if msg.get("media") and msg.get("caption"):
            await bot.send_cached_media(
                chat_id=sts.get('TO'),
                file_id=msg.get("media"),
                caption=msg.get("caption"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect")
            )
        else:
            await bot.copy_message(
                chat_id=sts.get('TO'),
                from_chat_id=sts.get('FROM'),
                caption=msg.get("caption"),
                message_id=msg.get("msg_id"),
                reply_markup=msg.get('button'),
                protect_content=msg.get("protect")
            )
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await copy(bot, msg, m, sts)
    except Exception as e:
        print(e)
        sts.add('deleted')

async def forward(bot: Client, msg: list, m: Message, sts: STS, protect: bool):
    try:
        await bot.forward_messages(
            chat_id=sts.get('TO'),
            from_chat_id=sts.get('FROM'),
            protect_content=protect,
            message_ids=msg
        )
    except FloodWait as e:
        await edit(m, 'Progressing', e.value, sts)
        await asyncio.sleep(e.value)
        await edit(m, 'Progressing', 10, sts)
        await forward(bot, msg, m, sts, protect)

PROGRESS = """
📈 Percentage: {0} %

♻️ Fetched: {1}

♻️ Forwarded: {2}

♻️ Remaining: {3}

♻️ Status: {4}

⏳️ ETA: {5}
"""

async def msg_edit(msg: Message, text: str, button: InlineKeyboardMarkup = None, wait: bool = None) -> Message:
    try:
        return await msg.edit(text, reply_markup=button)
    except MessageNotModified:
        pass
    except FloodWait as e:
        if wait:
            await asyncio.sleep(e.value)
            return await msg_edit(msg, text, button, wait)

async def edit(msg: Message, title: str, status: str, sts: STS):
    i = sts.get(full=True)
    status = 'Forwarding' if status == 10 else f"Sleeping {status} s" if str(status).isnumeric() else status
    percentage = "{:.0f}".format(float(i.fetched) * 100 / float(i.total))
    
    now = time.time()
    diff = int(now - i.start)
    speed = sts.divide(i.fetched, diff)
    elapsed_time = round(diff) * 1000
    time_to_completion = round(sts.divide(i.total - i.fetched, int(speed))) * 1000
    estimated_total_time = elapsed_time + time_to_completion
    
    progress = "◉{0}{1}".format(
        ''.join(["◉" for _ in range(math.floor(int(percentage) / 10))]),

import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import db
from translation import Translation
from .test import get_configs, update_configs, CLIENT, parse_buttons

app = Client("my_bot")  # Pastikan session sesuai

@app.on_message(filters.command('settings'))
async def settings(client, message):
    await message.delete()
    await message.reply_text(
        "<b>Change your settings as you wish</b>",
        reply_markup=main_buttons()
    )

@app.on_callback_query(filters.regex(r'^settings'))
async def settings_query(client, query):
    user_id = query.from_user.id
    _, type = query.data.split("#")
    buttons = [[InlineKeyboardButton('↩ Back', callback_data="settings#main")]]
    
    if type == "main":
        await query.message.edit_text(
            "<b>Change your settings as you wish</b>",
            reply_markup=main_buttons()
        )
    
    elif type == "bots":
        buttons = []
        _bot = await db.get_bot(user_id)
        if _bot is not None:
            buttons.append([InlineKeyboardButton(_bot['name'], callback_data=f"settings#editbot")])
        else:
            buttons.append([InlineKeyboardButton('✚ Add Bot ✚', callback_data="settings#addbot")])
            buttons.append([InlineKeyboardButton('✚ Add User Bot ✚', callback_data="settings#adduserbot")])
        buttons.append([InlineKeyboardButton('↩ Back', callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>My Bots</u></b>\n\n<b>You can manage your bots here</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type == "addbot":
        await query.message.delete()
        # Tambahkan implementasi untuk penambahan token bot
        bot = await CLIENT.add_bot(query)
        if bot is not True: return
        await query.message.reply_text(
            "<b>Bot token successfully added to the database</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

    elif type == "adduserbot":
        await query.message.delete()
        # Tambahkan implementasi untuk penambahan session user bot
        user = await CLIENT.add_session(query)
        if user is not True: return
        await query.message.reply_text(
            "<b>Session successfully added to the database</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type == "channels":
        buttons = []
        channels = await db.get_user_channels(user_id)
        for channel in channels:
            buttons.append([InlineKeyboardButton(f"{channel['title']}", callback_data=f"settings#editchannels_{channel['chat_id']}")])
        buttons.append([InlineKeyboardButton('✚ Add Channel ✚', callback_data="settings#addchannel")])
        buttons.append([InlineKeyboardButton('↩ Back', callback_data="settings#main")])
        await query.message.edit_text(
            "<b><u>My Channels</u></b>\n\n<b>You can manage your target chats here</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type == "addchannel":
        await query.message.delete()
        try:
            text = await client.send_message(user_id, "<b>❪ SET TARGET CHAT ❫\n\nForward a message from your target chat\n/cancel - cancel this process</b>")
            response = await client.listen(user_id, timeout=300)
            if response.text == "/cancel":
                await text.edit_text("<b>Process canceled</b>")
                return
            elif not response.forward_date:
                await text.edit_text("**This is not a forwarded message**")
                return
            else:
                chat_id = response.forward_from_chat.id
                title = response.forward_from_chat.title
                username = response.forward_from_chat.username
                username = f"@{username}" if username else "private"
            chat = await db.add_channel(user_id, chat_id, title, username)
            await text.edit_text(
                "<b>Successfully updated</b>" if chat else "<b>This channel is already added</b>",
                reply_markup=InlineKeyboardMarkup(buttons)
            )
        except asyncio.exceptions.TimeoutError:
            await text.edit_text('Process has been automatically cancelled', reply_markup=InlineKeyboardMarkup(buttons))
    
    elif type == "editbot":
        bot = await db.get_bot(user_id)
        TEXT = Translation.BOT_DETAILS if bot['is_bot'] else Translation.USER_DETAILS
        buttons = [
            [InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removebot")],
            [InlineKeyboardButton('↩ Back', callback_data="settings#bots")]
        ]
        await query.message.edit_text(
            TEXT.format(bot['name'], bot['id'], bot['username']),
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type == "removebot":
        await db.remove_bot(user_id)
        await query.message.edit_text(
            "<b>Successfully updated</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type.startswith("editchannels"):
        chat_id = type.split('_')[1]
        chat = await db.get_channel_details(user_id, chat_id)
        buttons = [
            [InlineKeyboardButton('❌ Remove ❌', callback_data=f"settings#removechannel_{chat_id}")],
            [InlineKeyboardButton('↩ Back', callback_data="settings#channels")]
        ]
        await query.message.edit_text(
            f"<b><u>📄 CHANNEL DETAILS</u></b>\n\n<b>- TITLE:</b> <code>{chat['title']}</code>\n<b>- CHANNEL ID:</b> <code>{chat['chat_id']}</code>\n<b>- USERNAME:</b> {chat['username']}",
            reply_markup=InlineKeyboardMarkup(buttons)
        )
    
    elif type.startswith("removechannel"):
        chat_id = type.split('_')[1]
        await db.remove_channel(user_id, chat_id)
        await query.message.edit_text(
            "<b>Successfully updated</b>",
            reply_markup=InlineKeyboardMarkup(buttons)
        )

def main_buttons():
    buttons = [
        [
            InlineKeyboardButton('🤖 Bᴏᴛs', callback_data='settings#bots'),
            InlineKeyboardButton('🏷 Cʜᴀɴɴᴇʟs', callback_data='settings#channels')
        ],
        [
            InlineKeyboardButton('🖋️ Cᴀᴘᴛɪᴏɴ', callback_data='settings#caption'),
            InlineKeyboardButton('🗃 MᴏɴɢᴏDB', callback_data='settings#database')
        ],
        [
            InlineKeyboardButton('🕵‍♀ Fɪʟᴛᴇʀs 🕵‍♀', callback_data='settings#filters'),
            InlineKeyboardButton('⏹ Bᴜᴛᴛᴏɴ', callback_data='settings#button')
        ],
        [
            InlineKeyboardButton('Exᴛʀᴀ Sᴇᴛᴛɪɴɢs 🧪', callback_data='settings#nextfilters')
        ],
        [
            InlineKeyboardButton('⫷ Bᴀᴄᴋ', callback_data='back')
        ]
    ]
    return InlineKeyboardMarkup(buttons)

def size_limit(limit):
    if str(limit) == "None":
        return None, ""
    elif str(limit) == "True":
        return True, "more than"
    else:
        return False, "less than"

def extract_btn(datas):
    i = 0
    btn = []
    if datas:
        for data in datas:
            if i >= 5:
                i = 0
            if i == 0:
                btn.append([InlineKeyboardButton(data, f'settings#alert_{data}')])
                i += 1
            elif i > 0 and i < 5:
                btn[-1].append(InlineKeyboardButton(data, f'settings#alert_{data}'))
                i += 1
    return btn

app.run()

import os
import re
import sys
import typing
import asyncio
import logging
from database import db
from config import Config, temp
from pyrogram import Client, filters
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from pyrogram.errors.exceptions.bad_request_400 import AccessTokenExpired, AccessTokenInvalid
from translation import Translation

from typing import Union, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

BTN_URL_REGEX = re.compile(r"(\[([^\[]+?)]\[buttonurl:/{0,2}(.+?)(:same)?])")
BOT_TOKEN_TEXT = "<b>1) create a bot using @BotFather\n2) Then you will get a message with bot token\n3) Forward that message to me</b>"
SESSION_STRING_SIZE = 351

class CLIENT:
    def __init__(self):
        self.api_id = Config.API_ID
        self.api_hash = Config.API_HASH
    
    def client(self, data, user=None):
        if user is None and not data.get('is_bot'):
            return Client("USERBOT", api_id=self.api_id, api_hash=self.api_hash, session_string=data.get('session'))
        elif user is True:
            return Client("USERBOT", api_id=self.api_id, api_hash=self.api_hash, session_string=data)
        else:
            return Client("BOT", api_id=self.api_id, api_hash=self.api_hash, bot_token=data.get('token'))
  
    async def add_bot(self, bot, message):
        user_id = int(message.from_user.id)
        msg = await bot.ask(chat_id=user_id, text=BOT_TOKEN_TEXT)
        if msg.text == '/cancel':
            return await msg.reply('<b>Process cancelled!</b>')
        if not msg.forward_date:
            return await msg.reply_text("<b>This is not a forwarded message</b>")
        if str(msg.forward_from.id) != "93372553":
            return await msg.reply_text("<b>This message was not forwarded from BotFather</b>")
        bot_token = re.findall(r'\d[0-9]{8,10}:[0-9A-Za-z_-]{35}', msg.text, re.IGNORECASE)
        bot_token = bot_token[0] if bot_token else None
        if not bot_token:
            return await msg.reply_text("<b>There is no bot token in that message</b>")
        try:
            _client = self.client(bot_token, False)
            await _client.start()
        except Exception as e:
            return await msg.reply_text(f"<b>BOT ERROR:</b> `{e}`")
        _bot = await _client.get_me()
        details = {
            'id': _bot.id,
            'is_bot': True,
            'user_id': user_id,
            'name': _bot.first_name,
            'token': bot_token,
            'username': _bot.username
        }
        await db.add_bot(details)
        return True
    
    async def add_session(self, bot, message):
        user_id = int(message.from_user.id)
        text = "<b>⚠️ DISCLAIMER ⚠️</b>\n\n<code>You can use your session for forwarding messages from private chat to another chat. Please add your Pyrogram session at your own risk. There is a chance that your account might get banned. My developer is not responsible if your account gets banned.</code>"
        await bot.send_message(user_id, text=text)
        msg = await bot.ask(chat_id=user_id, text="<b>Send your Pyrogram session.\nGet it from trusted sources.\n\n/cancel - Cancel the process</b>")
        if msg.text == '/cancel':
            return await msg.reply('<b>Process cancelled!</b>')
        if len(msg.text) < SESSION_STRING_SIZE:
            return await msg.reply('<b>Invalid session string</b>')
        try:
            client = self.client(msg.text, True)
            await client.start()
        except Exception as e:
            return await msg.reply_text(f"<b>USER BOT ERROR:</b> `{e}`")
        user = await client.get_me()
        details = {
            'id': user.id,
            'is_bot': False,
            'user_id': user_id,
            'name': user.first_name,
            'session': msg.text,
            'username': user.username
        }
        await db.add_bot(details)
        return True

@Client.on_message(filters.private & filters.command('reset'))
async def forward_tag(bot, m):
    default = await db.get_configs("01")
    temp.CONFIGS[m.from_user.id] = default
    await db.update_configs(m.from_user.id, default)
    await m.reply("Successfully reset settings ✔️")

@Client.on_message(filters.command('resetall') & filters.user(Config.BOT_OWNER_ID))
async def resetall(bot, message):
    users = await db.get_all_users()
    sts = await message.reply("**Processing**")
    TEXT = "Total: {}\nSuccess: {}\nFailed: {}\nExcept: {}"
    total, success, failed, already = 0, 0, 0, 0
    ERRORS = []
    async for user in users:
        user_id = user['id']
        default = await get_configs(user_id)
        default['db_uri'] = None
        total += 1
        if total % 10 == 0:
            await sts.edit(TEXT.format(total, success, failed, already))
        try:
            await db.update_configs(user_id, default)
            success += 1
        except Exception as e:
            ERRORS.append(e)
            failed += 1
    if ERRORS:
        await message.reply(ERRORS[:100])
    await sts.edit("Completed\n" + TEXT.format(total, success, failed, already))

async def get_configs(user_id):
    configs = await db.get_configs(user_id)
    return configs

async def update_configs(user_id, key, value):
    current = await db.get_configs(user_id)
    if key in ['caption', 'duplicate', 'db_uri', 'forward_tag', 'protect', 'file_size', 'size_limit', 'extension', 'keywords', 'button']:
        current[key] = value
    else:
        current['filters'][key] = value
    await db.update_configs(user_id, current)

def parse_buttons(text, markup=True):
    buttons = []
    for match in BTN_URL_REGEX.finditer(text):
        n_escapes = 0
        to_check = match.start(1) - 1
        while to_check > 0 and text[to_check] == "\\":
            n_escapes += 1
            to_check -= 1

        if n_escapes % 2 == 0:
            if bool(match.group(4)) and buttons:
                buttons[-1].append(InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", "")))
            else:
                buttons.append([InlineKeyboardButton(
                    text=match.group(2),
                    url=match.group(3).replace(" ", ""))])
    if markup and buttons:
        buttons = InlineKeyboardMarkup(buttons)
    return buttons if buttons else None

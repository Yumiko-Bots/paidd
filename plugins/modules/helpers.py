import asyncio
import json
import logging
import re
import sys
from urllib.parse import urlparse
import traceback
import aiohttp
import PyBypass as bypasser
from aiohttp import web
from mdisky import Mdisk
from pyrogram import Client
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait, MessageNotModified, PeerIdInvalid
from pyrogram.types import (InlineKeyboardButton, InlineKeyboardMarkup,
                            InputMediaPhoto, Message, BotCommand)
from shortzy import Shortzy

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

class temp(object):  # TrojanZ Idea of Temping
    BOT_USERNAME = None
    CANCEL = False
    FIRST_NAME = None
    START_TIME = None
    BANNED_USERS = []

class AsyncIter:
    def __init__(self, items):
        self.items = items

    async def __aiter__(self):
        for item in self.items:
            yield item

    async def __anext__(self):
        try:
            return next(self.iter)
        except StopIteration as e:
            raise StopAsyncIteration from e

async def create_inline_keyboard_markup(message: Message, method_func, user):
    if message.reply_markup:
        reply_markup = json.loads(str(message.reply_markup))
        buttons = []


        for markup in reply_markup["inline_keyboard"]:
            row_buttons = []
            for button_data in markup:
                if button_data.get("url"):
                    text = button_data["text"]
                    url = await method_func(user=user, text=button_data["url"])
                    row_buttons.append(InlineKeyboardButton(text, url=url))
                elif button_data.get("callback_data"):
                    row_buttons.append(InlineKeyboardButton(text=button_data["text"], callback_data=button_data["callback_data"]))
                else:
                    row_buttons.append(InlineKeyboardButton(text=button_data["text"], switch_inline_query_current_chat=button_data["switch_inline_query_current_chat"]))

            buttons.append(row_buttons)
        return InlineKeyboardMarkup(buttons)

async def update_stats(m: Message, method):
    if m.caption:
        message = m.caption.html
    else:
        message = m.text.html

    mdisk_links = re.findall(
        r'https?://mdisk.me[^\s`!()\[\]{};:".,<>?«»“”‘’]+', message
    )
    droplink_links = await extract_link(message)
    total_links = len(droplink_links)
    await db.update_posts(1)
    if method == "mdisk":
        droplink_links = []
    if method == "shortener":
        mdisk_links = []
    await db.update_links(total_links, len(droplink_links), len(mdisk_links))

async def main_convertor_handler(
    message: Message, edit_caption: bool = False, user=None
):

    """
    This function is used to convert a message to a different format

    :param message: The message object that the user sent
    :type message: Message
    :param type: str - The type of the media to be converted
    :param edit_caption: If you want to edit the caption of the message, set this to True, defaults to
    False
    :type edit_caption: bool (optional)
    :param user: The user who sent the message
    """
    if user:
        header_text = (
            user["header_text"].replace(
                r"\n", "\n") if user["is_header_text"] else ""
        )
        footer_text = (
            user["footer_text"].replace(
                r"\n", "\n") if user["is_footer_text"] else ""
        )
        username = user["username"] if user["is_username"] else None
        banner_image = user["banner_image"] if user["is_banner_image"] else None

    caption = None

    if message.text:
        caption = message.text.html
    elif message.caption:
        caption = message.caption.html

    # Checking if the message has any link or not. If it doesn't have any link, it will return.
    if len(await extract_link(caption)) <= 0 and not message.reply_markup:
        return

    user_method = user["method"]

    # Checking if the user has set his method or not. If not, it will reply with a message.
    if user_method is None:
        return await message.reply(text="Set your /method first")

    # Bypass Links
    caption = await bypass_handler(caption)

    # A dictionary which contains the methods to be called.
    METHODS = {
        "mdisk": mdisk_api_handler,
        "shortener": replace_link,
        "mdlink": mdisk_droplink_convertor,
    }

    # Replacing the username with your username.
    caption = await replace_username(caption, username)

    # Getting the function for the user's method
    method_func = METHODS[user_method]

    # converting urls
    shortenedText = await method_func(user, caption)
    reply_markup = await create_inline_keyboard_markup(message, method_func, user=user)
    shortenedText = f"{header_text}\n{shortenedText}\n{footer_text}"
    if message.media:
        medias = getattr(message, message.media.value)
        fileid = medias.file_id
        if message.photo and banner_image:
            fileid = banner_image
            if edit_caption:
                fileid = InputMediaPhoto(banner_image, caption=shortenedText)

    if message.text:
        if user_method in ["shortener", "mdlink"] and "|" in caption:
            regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))\s\|\s([a-zA-Z0-9_]){,30}"
            if custom_alias := re.match(regex, caption):
                custom_alias = custom_alias[0].split("|")
                alias = custom_alias[1].strip()
                url = custom_alias[0].strip()
                shortenedText = await method_func(user, url, alias=alias)

        if edit_caption:
            try:
                return await message.edit(
                    shortenedText, disable_web_page_preview=True, reply_markup=reply_markup
                )
            except MessageNotModified:
                return

        return await message.reply(
            shortenedText,
            disable_web_page_preview=True,
            reply_markup=reply_markup,
            quote=True,
            parse_mode=ParseMode.HTML,
        )

    elif message.media:
        if edit_caption:
            if banner_image and message.photo:
                return await message.edit_media(media=fileid)

            try:
                await message.edit_caption(
                    shortenedText, reply_markup=reply_markup, parse_mode=ParseMode.HTML
                )
                return
            except MessageNotModified:
                return

        meta = {
            "caption": shortenedText,
            "reply_markup": reply_markup,
            "quote": True,
            "parse_mode": ParseMode.HTML,
        }
        if message.document:
            return await message.reply_document(document=fileid, **meta)

        elif message.photo:
            return await message.reply_photo(photo=fileid, **meta)

        elif message.video:
            return await message.reply_video(video=fileid, **meta)

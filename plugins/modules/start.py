from pyrogram import filters, InlineKeyboardButton, InlineKeyboardMarkup, UserNotParticipant
from pyrogram.types import Message
from plugins import corn 

force_channel = "-1001947211484"

@corn.on_message(filters.command("start") & filters.private)
async def start(corn, message: Message):
    if force_channel:
        try:
            user = await corn.get_chat_member(force_channel, message.from_user.id)
            if user.status == "kicked":
                await message.reply_text("You are banned.")
                return
        except UserNotParticipant:
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("Join Channel", url=f"https://t.me/{force_channel}")]
            ])
            await message.reply_text("You are not joined in my channel. Please join the channel to use me.", reply_markup=keyboard)
            return

    await message.reply_text(f"Hello {message.from_user.mention}\n\nI am a private files save bot. I can save private files on certain channels, and other users can access them from a special link.")

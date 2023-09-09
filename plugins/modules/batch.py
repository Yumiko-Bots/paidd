import asyncio
import datetime
import logging
from database.users import get_user
from pyrogram import Client, filters
from pyrogram.errors import ChatWriteForbidden, PeerIdInvalid, FloodWait
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from plugins.modules.helpers import main_convertor_handler, update_stats, AsyncIter, temp

SUDO_USERS = [5954494174, 5857041668]

logger = logging.getLogger(__name__)

lock = asyncio.Lock()

cancel_button = [[InlineKeyboardButton(
    "Cancel 🔐", callback_data="cancel_process")]]


@Client.on_message(filters.private & filters.command("batch") & filters.user(SUDO_USERS))
async def batch(c, m: Message):
    if m.from_user.id not in SUDO_USERS:
        return await m.reply_text("Works only for Sudo users")

    if len(m.command) < 2:
        await m.reply_text("""Need to shorten or convert links from all of your channel's posts? I've got you covered! Just make me an admin in your channel and use the following command:

<code>/batch [channel id or username]</code>

For example: <code>/batch -100xxx</code>

I'll handle the rest and get those links shortened or converted in a short time!""",
                          )
    else:
        channel_id = m.command[1]
        if channel_id.startswith("@"):
            channel_id = channel_id.split("@")[1]

        buttons = [
            [
                InlineKeyboardButton(
                    "Batch Short 🏕", callback_data=f"batch#{channel_id}"
                )
            ],
            [InlineKeyboardButton("Cancel 🔐", callback_data="cancel")],
        ]

        return await m.reply(
            text=f"Are you sure you want to batch short?\n\nChannel: {channel_id}",
            reply_markup=InlineKeyboardMarkup(buttons),
        )


@Client.on_callback_query(
    filters.regex(r"^cancel") | filters.regex(r"^batch") & filters.user(SUDO_USERS)
)
async def batch_handler(c: Client, m: CallbackQuery):
    if m.data == "cancel":
        await m.message.delete()
        return
    elif m.data.startswith("batch"):
        if lock.locked():
            return await m.answer(
                "Wait until previous process complete.", show_alert=True
            )

        channel_id = int(m.data.split("#")[1])
        try:
            txt = await c.send_message(channel_id, ".")
            id = txt.id
            await txt.delete()

        except ChatWriteForbidden:
            return await m.message.edit("Bot is not an admin in the given channel")
        except PeerIdInvalid:
            return await m.message.edit("Given channel ID is invalid")
        except Exception as e:
            logging.exception(e)
            return await m.message.edit(e)

        start_time = datetime.datetime.now()
        txt = await m.message.edit(
            text=f"Batch Shortening Started!\n\n Channel: {channel_id}\n\nTo Cancel /cancel",
        )
        logger.info(f"Batch Shortening Started for {channel_id}")

        success = 0
        fail = 0
        total = 0
        empty = 0

        total_messages = range(1, id)
        temp.CANCEL = False
        try:
            for i in range(0, len(total_messages), 200):
                channel_posts = AsyncIter(
                    await c.get_messages(channel_id, total_messages[i: i + 200])
                )
                if temp.CANCEL:
                    break
                async with lock:
                    async for message in channel_posts:
                        if temp.CANCEL:
                            break
                        if message.text or message.caption:
                            try:
                                await main_convertor_handler(
                                    message=message,
                                    edit_caption=True,
                                    user=user,
                                )
                            except FloodWait as e:
                                await asyncio.sleep(e.value)
                                await main_convertor_handler(
                                    message=message,
                                    edit_caption=True,
                                    user=user,
                                )

                            except Exception as e:
                                logger.error(e, exc_info=True)
                                fail += 1
                            success += 1
                            await update_stats(message, user_method)

                            await asyncio.sleep(1)
                        else:
                            empty += 1
                        total += 1

                        if total % 10 == 0:
                            msg = f"Batch Shortening in Process !\n\nTotal: {total}\nSuccess: {success}\nFailed: {fail}\nEmpty: {empty}\n\nTo cancel the batch: /cancel"
                            await txt.edit(msg)
        except Exception as e:
            logger.error(e, exc_info=True)
            await m.message.reply(
                f"Error Occured while processing batch: `{e.message}`"
            )
        finally:
            end_time = datetime.datetime.now()
            await asyncio.sleep(10)
            t = end_time - start_time
            time_taken = str(datetime.timedelta(seconds=t.seconds))
            msg = f"Batch Shortening Completed!\n\nTime Taken - `{time_taken}`\n\nTotal: `{total}`\nSuccess: `{success}`\nFailed: `{fail}`\nEmpty: `{empty}`"
            await txt.edit(msg)
            logger.info(f"Batch Shortening Completed for {channel_id}")


@Client.on_message(filters.private & filters.command("cancel") & filters.user(SUDO_USERS))
async def stop_button(c, m):
    temp.CANCEL = True
    msg = await c.send_message(
        text="<i>Trying To Stoping.....</i>", chat_id=m.chat.id
    )

    await asyncio.sleep(5)
    await msg.edit("Batch Shortening Stopped Successfully 👍")
    logger.info("Batch Shortening Stopped Successfully 👍")

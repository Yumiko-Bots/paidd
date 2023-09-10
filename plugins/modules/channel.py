import logging

from Config import config
from database.users import get_user
from pyrogram import Client, filters
from plugins.modules.helpers import main_convertor_handler, update_stats

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

@Client.on_message(
    ~filters.forwarded
    & filters.chat(config.CHANNEL_ID)
    & (filters.channel | filters.group)
    & filters.incoming
    & ~filters.private
    & ~filters.forwarded
)
async def channel_link_handler(c: Client, message):
    if config.CHANNELS:
        user = await get_user(config.OWNER_ID)
        user_method = user["method"]

        try:
            await main_convertor_handler(message, True, user=user)
            await update_stats(message, user_method)
        except Exception as e:
            logger.exception(e, exc_info=True)

@Client.on_message(filters.command("test") & filters.user(config.OWNER_ID))
async def test(c: Client, message):
    m_id = 3012
    c_id = 0
    message = await c.get_messages(c_id, m_id)
    user = await get_user(config.OWNER_ID)
    await main_convertor_handler(message, True, user)

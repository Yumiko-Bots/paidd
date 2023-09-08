from pyrogram import Client, filters, idle
from Config import config

corn = Client(
       ":corn:",
       api_id=config.API_ID,
       api_hash=config.API_HASH,
       bot_token=config.BOT_TOKEN,
       plugins=dict(root="plugins.modules")
)
print("Bot started!")
corn.start()
idle()

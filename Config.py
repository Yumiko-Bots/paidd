from os import path, getenv
import os
from dotenv import load_dotenv

load_dotenv()



def is_enabled(value, default):
    if value.lower() in ["true", "yes", "1", "enable", "y"]:
        return True
    elif value.lower() in ["false", "no", "0", "disable", "n"]:
        return False
    else:
        return default



class config:

    API_ID = "8623612"
    API_HASH = "06ea2889c5517eb64017b032d667e29f"
    BOT_TOKEN = "6265217004:AAE_yot4SqUFrvBa1IJXgRy-kaeZm9z3Xwk"
    SUDO_USERS = 5954494174, 5857041668
    CHANNELS = is_enabled((os.environ.get("CHANNELS", "True")), True)
    CHANNEL_ID = (
        [int(i.strip()) for i in os.environ.get("CHANNEL_ID", "-1001947211484").split(" ")]
        if os.environ.get("CHANNEL_ID")
        else []
    )
    OWNER_ID = int(os.environ.get("OWNER_ID", "5857041668"))
    SUDO_USERS.append(OWNER_ID) if OWNER_ID not in SUDO_USERS else []
    DATABASE_NAME = os.environ.get("DATABASE_NAME", "cluster0")
    DATABASE_URL = os.environ.get("DATABASE_URL", "mongodb+srv://Amala203145:Amala2031456@cluster0.t9ibfge.mongodb.net/?retryWrites=true&w=majority")  
    BOT_USERNAME = os.environ.get("BOT_USERNAME", "fuckedusernamesbot")
    DB_CHANNEL = int(os.environ.get("DB_CHANNEL", "-1001947211484"))

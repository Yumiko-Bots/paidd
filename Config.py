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
    DATABASE_URL = 'mongodb+srv://marcopetrali657:marcopetrali657@cluster0.dwztggn.mongodb.net/?retryWrites=true&w=majority'
    DATABASE_NAME = "marcopetrali657"

    CHANNELS = is_enabled((os.environ.get("CHANNELS", "True")), True)
    CHANNEL_ID = (
        [int(i.strip()) for i in os.environ.get("CHANNEL_ID").split(" ")]
        if os.environ.get("CHANNEL_ID")
        else []
    )
    OWNER_ID = int(os.environ.get("OWNER_ID"))
    SUDO_USERS.append(OWNER_ID) if OWNER_ID not in SUDO_USERS else []


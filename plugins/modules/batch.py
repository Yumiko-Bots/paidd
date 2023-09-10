import re, os, json, base64, logging
from pyrogram import filters, Client, enums
from pyrogram.errors.exceptions.bad_request_400 import ChannelInvalid, UsernameInvalid, UsernameNotModified, ChatAdminRequired
from Config import config
from database.ia_filterdb import unpack_new_file_id, save_file
from plugins import corn
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class temp(object):
    BANNED_USERS = []
    BANNED_CHATS = []
    CURRENT = 0
    CANCEL = False
    MELCOW = {}
    U_NAME = None
    B_NAME = None
    SETTINGS = {}
    GP_BUTTONS = {}
    PM_BUTTONS = {}
    PM_SPELL = {}
    GP_SPELL = {}


async def allowed(_, __, message):
    if config.PUBLIC_FILE_STORE:
        return True
    if message.from_user and message.from_user.id in config.SUDO_USERS:
        return True
    return False

@Client.on_message(filters.command(['link', 'plink']) & filters.create(allowed))
async def gen_link_s(bot, message):
    replied = message.reply_to_message
    if not replied:
        return await message.reply('Reply to a message to get a shareable link.')
    file_type = replied.media
    if file_type not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
        return await message.reply("Reply to a supported media")
    if message.has_protected_content and message.chat.id not in config.SUDO_USERS:
        return await message.reply("okDa")
    file_id, ref = unpack_new_file_id((getattr(replied, file_type.value)).file_id)
    string = 'filep_' if message.text.lower().strip() == "/plink" else 'file_'
    string += file_id
    outstr = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
    await message.reply(f"Here is your Link:\nhttps://t.me/{config.BOT_USERNAME}?start={outstr}")

@Client.on_message(filters.command(['batch', 'pbatch']) & filters.create(allowed))
async def gen_link_batch(bot, message):
    if " " not in message.text:
        return await message.reply("Use correct format.\nExample <code>/batch https://t.me/santhutech/1 https://t.me/santhutech/12</code>.")
    links = message.text.strip().split(" ")
    if len(links) != 3:
        return await message.reply("Use correct format.\nExample <code>/batch https://t.me/santhutech/1 https://t.me/santhutech/12</code>.")
    cmd, first, last = links
    regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
    match = regex.match(first)
    if not match:
        return await message.reply('Invalid link')
    f_chat_id = match.group(4)
    f_msg_id = int(match.group(5))
    if f_chat_id.isnumeric():
        f_chat_id  = int(("-100" + f_chat_id))

    match = regex.match(last)
    if not match:
        return await message.reply('Invalid link')
    l_chat_id = match.group(4)
    l_msg_id = int(match.group(5))
    if l_chat_id.isnumeric():
        l_chat_id  = int(("-100" + l_chat_id))

    if f_chat_id != l_chat_id:
        return await message.reply("Chat ids not matched.")
    try:
        chat_id = (await bot.get_chat(f_chat_id)).id
    except ChannelInvalid:
        return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified):
        return await message.reply('Invalid Link specified.')
    except Exception as e:
        return await message.reply(f'Errors - {e}')

    sts = await message.reply("Generating link for your message.\nThis may take time depending upon the number of messages")
    if chat_id in config.FILE_STORE_CHANNEL:
        string = f"{f_msg_id}_{l_msg_id}_{chat_id}_{cmd.lower().strip()}"
        b_64 = base64.urlsafe_b64encode(string.encode("ascii")).decode().strip("=")
        keyboardd = InlineKeyboardMarkup( [[
            InlineKeyboardButton("Here is Your Link", url="https://t.me/{config.BOT_USERNAME}?start=DSTORE-{b_64}}")
            ]]
            )
        return await sts.edit(f"below your link", reply_markup=keyboardd)

    FRMT = "Generating Link...\nTotal Messages: `{total}`\nDone: `{current}`\nRemaining: `{rem}`\nStatus: `{sts}`"

    outlist = []

    # file store without db channel
    og_msg = 0
    tot = 0
    try:
        messages = await bot.get_messages(f_chat_id, l_msg_id, f_msg_id)
        for message in messages:
            tot += 1
            if message.empty or message.service:
                continue
            if not message.media:
                # only media messages supported.
                continue
            try:
                file_type = message.media
                file = getattr(message, file_type.value)
                caption = getattr(message, 'caption', '')
                if caption:
                    caption = caption.html
                if file:
                    file = {
                        "file_id": file.file_id,
                        "caption": caption,
                        "title": getattr(file, "file_name", ""),
                        "size": file.file_size,
                        "protect": cmd.lower().strip() == "/pbatch",
                    }

                    og_msg += 1
                    outlist.append(file)
            except:
                pass
            if not og_msg % 20:
                try:
                    await sts.edit(FRMT.format(total=l_msg_id-f_msg_id, current=tot, rem=((l_msg_id-f_msg_id) - tot), sts="Saving Messages"))
                except:
                    pass
    except Exception as e:
        await message.reply(f'Error while fetching messages - {e}')
    
    with open(f"batchmode_{message.from_user.id}.json", "w+") as out:
        json.dump(outlist, out)
    post = await bot.send_document(config.LOG_CHANNEL, f"batchmode_{message.from_user.id}.json", file_name="Batch.json", caption="⚠️Generated for filestore.")
    os.remove(f"batchmode_{message.from_user.id}.json")
    file_id, ref = unpack_new_file_id(post.document.file_id)
    keyboard = InlineKeyboardMarkup( [[
          InlineKeyboardButton("Batch Link", url="https://t.me/{config.BOT_USERNAME}?start=BATCH-{file_id}")
          ]]
          )
    await sts.edit(f"Here is your link\nContains `{og_msg}` files.", reply_markup=keyboard)

@Client.on_message(filters.chat(config.CHANNELS) & (filters.document | filters.video | filters.audio))         
async def media(bot, message):
    for file_type in ("document", "video", "audio"):
        media = getattr(message, file_type, None)
        if media is not None: break
    else: return
    media.file_type = file_type
    media.caption = message.caption
    await save_file(media)

@Client.on_callback_query(filters.regex(r'^index'))
async def index_files(bot, query):
    if query.data.startswith('index_cancel'):
        temp.CANCEL = True
        return await query.answer("Cᴀɴᴄᴇʟʟɪɴɢ Iɴᴅᴇxɪɴɢ", show_alert=True)
        
    perfx, chat, lst_msg_id = query.data.split("#")
    if lock.locked():
        return await query.answer('Wᴀɪᴛ Uɴᴛɪʟ Pʀᴇᴠɪᴏᴜs Pʀᴏᴄᴇss Cᴏᴍᴘʟᴇᴛᴇ', show_alert=True)
    msg = query.message
    button = InlineKeyboardMarkup([[
        InlineKeyboardButton('🚫 ᴄᴀɴᴄᴇʟʟ', "index_cancel")
    ]])
    await msg.edit("ɪɴᴅᴇxɪɴɢ ɪs sᴛᴀʀᴛᴇᴅ ✨", reply_markup=button)                        
    try: chat = int(chat)
    except: chat = chat
    await index_files_to_db(int(lst_msg_id), chat, msg, bot)


@Client.on_message((filters.forwarded | (filters.regex("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")) & filters.text ) & filters.private & filters.incoming & filters.user(config.SUDO_USERS))
async def send_for_index(bot, message):
    if message.text:
        regex = re.compile("(https://)?(t\.me/|telegram\.me/|telegram\.dog/)(c/)?(\d+|[a-zA-Z_0-9]+)/(\d+)$")
        match = regex.match(message.text)
        if not match: return await message.reply('Invalid link')
        chat_id = match.group(4)
        last_msg_id = int(match.group(5))
        if chat_id.isnumeric(): chat_id  = int(("-100" + chat_id))
    elif message.forward_from_chat.type == enums.ChatType.CHANNEL:
        last_msg_id = message.forward_from_message_id
        chat_id = message.forward_from_chat.username or message.forward_from_chat.id
    else: return
    try: await bot.get_chat(chat_id)
    except ChannelInvalid: return await message.reply('This may be a private channel / group. Make me an admin over there to index the files.')
    except (UsernameInvalid, UsernameNotModified): return await message.reply('Invalid Link specified.')
    except Exception as e: return await message.reply(f'Errors - {e}')
    try: k = await bot.get_messages(chat_id, last_msg_id)
    except: return await message.reply('Make Sure That Iam An Admin In The Channel, if channel is private')
    if k.empty: return await message.reply('This may be group and iam not a admin of the group.')
    buttons = InlineKeyboardMarkup([[
        InlineKeyboardButton('✨ ʏᴇꜱ', callback_data=f'index#{chat_id}#{last_msg_id}')
        ],[
        InlineKeyboardButton('🚫 ᴄʟᴏꜱᴇ', callback_data='close_data')
    ]])               
    await message.reply(f'Do You Want To Index This Channel/ Group ?\n\nChat ID/ Username: <code>{chat_id}</code>\nLast Message ID: <code>{last_msg_id}</code>', reply_markup=buttons)
    

@Client.on_message(filters.command('setskip') & filters.user(config.SUDO_USERS))
async def set_skip_number(bot, message):
    if len(message.command) == 2:
        try: skip = int(message.text.split(" ", 1)[1])
        except: return await message.reply("Skip Number Should Be An Integer.")
        await message.reply(f"Successfully Set Skip Number As {skip}")
        temp.CURRENT = int(skip)
    else:
        await message.reply("Give Me A Skip Number")


async def index_files_to_db(lst_msg_id, chat, msg, bot):
    total_files = 0
    duplicate = 0
    errors = 0
    deleted = 0
    no_media = 0
    unsupported = 0
    async with lock:
        try:
            current = temp.CURRENT
            temp.CANCEL = False
            async for message in bot.iter_messages(chat, lst_msg_id, temp.CURRENT):
                if temp.CANCEL:
                    await msg.edit(f"Successfully Cancelled!!\n\nSaved <code>{total_files}</code> files to dataBase!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>")
                    break
                current += 1
                if current % 100 == 0:
                    can = [[InlineKeyboardButton('Cancel', callback_data='index_cancel')]]
                    reply = InlineKeyboardMarkup(can)
                    try:
                        await msg.edit_text(text=f"Total Messages Fetched: <code>{current}</code>\nTotal Messages Saved: <code>{total_files}</code>\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>", reply_markup=reply)       
                    except FloodWait as t:
                        await asyncio.sleep(t.value)
                        await msg.edit_text(text=f"Total Messages Fetched: <code>{current}</code>\nTotal Messages Saved: <code>{total_files}</code>\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media messages skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>", reply_markup=reply)                          
                if message.empty:
                    deleted += 1
                    continue
                elif not message.media:
                    no_media += 1
                    continue
                elif message.media not in [enums.MessageMediaType.VIDEO, enums.MessageMediaType.AUDIO, enums.MessageMediaType.DOCUMENT]:
                    unsupported += 1
                    continue
                media = getattr(message, message.media.value, None)
                if not media:
                    unsupported += 1
                    continue
                media.file_type = message.media.value
                media.caption = message.caption
                aynav, vnay = await save_file(media)
                if aynav:
                    total_files += 1
                elif vnay == 0:
                    duplicate += 1
                elif vnay == 2:
                    errors += 1       
        except Exception as e:
            logger.exception(e)
            await msg.edit(f'Error: {e}')
        else:
            await msg.edit(f'Succesfully Saved <code>{total_files}</code> To Database!\nDuplicate Files Skipped: <code>{duplicate}</code>\nDeleted Messages Skipped: <code>{deleted}</code>\nNon-Media Messages Skipped: <code>{no_media + unsupported}</code>(Unsupported Media - `{unsupported}` )\nErrors Occurred: <code>{errors}</code>')

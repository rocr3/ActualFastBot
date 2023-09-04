import datetime
import os
import re
import json
import base64
import logging
import random
import asyncio
from Movies.database.quickdb import add_verify_user, find_all_file, find_verify_user
from config import *
from script import script
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Movies.database.media import Media, get_file_details, unpack_new_file_id
from Movies.database.chats import db
from Movies.utils import get_settings, get_shortlink, get_size, is_subscribed, replace_username, save_group_settings, temp
from Movies.database.connections import active_connection


logger = logging.getLogger(__name__)

BATCH_FILES = {}

# -------------------------------------------------------------------------------------------------- #

BOT_IMG = (
    "https://graph.org/file/516f3a3e2727af26bda21.jpg",
    "https://graph.org/file/ffed08551de347082e15a.jpg",
    "https://graph.org/file/ada30633cff1ba008642a.jpg",
    "https://graph.org/file/9b4341bc6fa5257c3a7f0.jpg",
    "https://graph.org/file/6bae7d13964b4c9e43868.jpg",
    "https://graph.org/file/7ee7dbff58183d873375f.jpg",
    "https://graph.org/file/5b10c55815dfb9c7499ff.jpg",
    "https://graph.org/file/09449c99f2c7032e38364.jpg",
    "https://graph.org/file/4a1999ed92de19f6755d3.jpg",
    "https://graph.org/file/2ecc6823e7422c08a5eb4.jpg",
    "https://graph.org/file/9346461a8b314200ba147.jpg",
    "https://graph.org/file/22e76bae032878315b9c2.jpg",
    "https://graph.org/file/9549c21e25f05e03daeb2.jpg",
    "https://graph.org/file/d29c0cb5c726a54560685.jpg",
    "https://graph.org/file/0403a2d2aa123a4736f12.jpg",
    "https://graph.org/file/9b4cce8881278d5989030.jpg",
    "https://graph.org/file/bfa3fa82b058494372360.jpg",
    "https://graph.org/file/f615cb3c840a180b44f0b.jpg",
    "https://graph.org/file/a715ee9379004c1a712eb.jpg",
    "https://graph.org/file/585535ad3248ec5748821.jpg",
    "https://graph.org/file/2455fc4b9f893d75e311b.jpg",

)


DOW_IMG = (
    "https://graph.org/file/d20384853714d25393e6f.jpg",
    "https://graph.org/file/5d773bacf2a94c905add3.jpg",
    "https://graph.org/file/259691dc93cecb612680c.jpg",

)


# -------------------------------------------------------------------------------------------------- #


# -------------------» sᴛᴀʀᴛ «-------------------- #

@Client.on_message(filters.command("start") & filters.incoming)
async def start(client, message):
    if message.chat.type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        buttons = [
            [
                InlineKeyboardButton(
                    'ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ', url='http://t.me/{temp.U_NAME}?startgroup=true')
            ],
            [
                InlineKeyboardButton(
                    'sᴜᴘᴘᴏʀᴛ', url=f"https://t.me/joinnowearn"),
            ]
        ]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
        await asyncio.sleep(2)
        if not await db.get_chat(message.chat.id):
            total = await client.get_chat_members_count(message.chat.id)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))
            await db.add_chat(message.chat.id, message.chat.title)
        return
    emo = None
    if len(message.command) >= 2 and "uvew_" in message.command[1] or "cms_" in message.command[1]:
        emo = await message.reply_text("Genrating your link ...")
    if not await db.is_user_exist(message.from_user.id):
        await db.add_user(message.from_user.id, message.from_user.first_name)
        await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
    if len(message.command) != 2:
        buttons = [[
            InlineKeyboardButton('🍟 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs 🍟',
                                 url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton(
                '🔍 sᴇᴀʀᴄʜ 🔍', switch_inline_query_current_chat=''),
            InlineKeyboardButton(
                '🌼 ᴜᴘᴅᴀᴛᴇs 🌼', url='https://t.me/Trickyakash5213')
        ], [
            InlineKeyboardButton('🍄 ʜᴇʟᴘ 🍄', callback_data='help'),
            InlineKeyboardButton('🔰 ᴀʙᴏᴜᴛ 🔰', callback_data='about')
        ], [
            InlineKeyboardButton(
                ' ᴄᴏɴɴᴇᴄᴛ ʏᴏᴜʀ sʜᴏʀᴛʟɪɴᴋ ғʀᴇᴇ ', url='https://t.me/joinnowearn/82')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        m = await message.reply_sticker("CAACAgUAAxkBAAINdmL9uWnC3ptj9YnTjFU4YGr5dtzwAAIEAAPBJDExieUdbguzyBAeBA")
        await asyncio.sleep(1)
        await m.delete()
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(
                message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return
    if AUTH_CHANNEL and not await is_subscribed(client, message):
        try:
            invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
        except ChatAdminRequired:
            logger.error("ᴍᴀᴋᴇ sᴜʀᴇ ʙᴏᴛ ɪs ᴀᴅᴍɪɴ ɪɴ ғᴏʀᴄᴇsᴜʙ ᴄʜᴀɴɴᴇʟ.")
            return
        btn = [
            [
                InlineKeyboardButton(
                    "🤖 ᴊᴏɪɴ ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ 🤖", url=invite_link.invite_link
                )
            ]
        ]
        if message.command[1] != "subscribe":
            try:
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub'
                btn.append([InlineKeyboardButton(
                    " 🔄 ᴛʀʏ ᴀɢᴀɪɴ", callback_data=f"{pre}#{file_id}")])
            except (IndexError, ValueError):
                btn.append([InlineKeyboardButton(
                    " 🔄 ᴛʀʏ ᴀɢᴀɪɴ", url=f"https://t.me/{temp.U_NAME}?start={message.command[1]}")])
        if emo:
            await emo.delete()
        await client.send_message(
            chat_id=message.from_user.id,
            text="**ᴊᴏɪɴ ᴏᴜʀ ᴍᴏᴠɪᴇs ᴜᴘᴅᴀᴛᴇs ᴄʜᴀɴɴᴇʟ ᴛᴏ ᴜsᴇ ᴛʜɪs ʙᴏᴛ !!**",
            reply_markup=InlineKeyboardMarkup(btn),
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return

    if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
        buttons = [[
            InlineKeyboardButton('🍟 ᴀᴅᴅ ᴍᴇ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘs 🍟',
                                 url=f'http://t.me/{temp.U_NAME}?startgroup=true')
        ], [
            InlineKeyboardButton(
                '🔍 sᴇᴀʀᴄʜ 🔍', switch_inline_query_current_chat=''),
            InlineKeyboardButton(
                '🌼 ᴜᴘᴅᴀᴛᴇs 🌼', url='https://t.me/Trickyakash5213')
        ], [
            InlineKeyboardButton('🍄 ʜᴇʟᴘ 🍄', callback_data='help'),
            InlineKeyboardButton('🔰 ᴀʙᴏᴜᴛ 🔰', callback_data='about')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await message.reply_photo(
            photo=random.choice(PICS),
            caption=script.START_TXT.format(
                message.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )
        return

    data = message.command[1]
    try:
        pre, file_id = data.split('_', 1)
    except:
        file_id = data
        pre = ""
    if data.split("-", 1)[0] == "BATCH":
        sts = await message.reply("<b>ᴀᴄᴄᴇssɪɴɢ ғɪʟᴇs.../</b>")
        file_id = data.split("-", 1)[1]
        msgs = BATCH_FILES.get(file_id)
        if not msgs:
            file = await client.download_media(file_id)
            try:
                with open(file) as file_data:
                    msgs = json.loads(file_data.read())
            except:
                await sts.edit("FAILED")
                return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
            os.remove(file)
            BATCH_FILES[file_id] = msgs
        for msg in msgs:
            title = msg.get("title")
            size = get_size(int(msg.get("size", 0)))
            f_caption = msg.get("caption", "")
            if BATCH_FILE_CAPTION:
                try:
                    f_caption = BATCH_FILE_CAPTION.format(
                        file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                except Exception as e:
                    logger.exception(e)
                    f_caption = f_caption
            if f_caption is None:
                f_caption = f"{title}"
            try:
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                )
            except FloodWait as e:
                await asyncio.sleep(e.x)
                logger.warning(f"Floodwait of {e.x} sec.")
                await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=msg.get("file_id"),
                    caption=f_caption,
                    protect_content=msg.get('protect', False),
                )
            except Exception as e:
                logger.warning(e, exc_info=True)
                continue
            await asyncio.sleep(1)
        await sts.delete()
        return
    elif data.split("-", 1)[0] == "DSTORE":
        sts = await message.reply("<b>ᴀᴄᴄᴇssɪɴɢ ғɪʟᴇs.../</b>")
        b_string = data.split("-", 1)[1]
        decoded = (base64.urlsafe_b64decode(
            b_string + "=" * (-len(b_string) % 4))).decode("ascii")
        try:
            f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
        except:
            f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
            protect = "/pbatch" if PROTECT_CONTENT else "batch"
        diff = int(l_msg_id) - int(f_msg_id)
        async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
            if msg.media:
                media = getattr(msg, msg.media.value)
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption = BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(
                            media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                    except Exception as e:
                        logger.exception(e)
                        f_caption = getattr(msg, 'caption', '')
                else:
                    media = getattr(msg, msg.media.value)
                    file_name = getattr(media, 'file_name', '')
                    f_caption = getattr(msg, 'caption', file_name)
                try:
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            elif msg.empty:
                continue
            else:
                try:
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                except Exception as e:
                    logger.exception(e)
                    continue
            await asyncio.sleep(1)
        return await sts.delete()

    elif data.split("_", 1)[0] == "uvew":
        datas = data.replace('uvew_', '')
        time, file_id = datas.split('x_y_z')
        uvew = await add_verify_user(message.from_user.id, time)
        button = [[
            InlineKeyboardButton("✅ Get File ✅",
                                 url=f"https://telegram.me/{temp.U_NAME}?start=files_{file_id}")
        ]]
        reply_markup = InlineKeyboardMarkup(button)
        if uvew:
            await emo.edit_text(text=f"𝙔𝙤𝙪 𝙎𝙪𝙘𝙘𝙚𝙨𝙛𝙪𝙡𝙡𝙮 𝙑𝙚𝙧𝙞𝙛𝙞𝙚𝙙 𝙁𝙤𝙧 12 𝙝𝙤𝙪𝙧𝙨 🚀\n𝘾𝙡𝙞𝙘𝙠 𝘽𝙚𝙡𝙤𝙬 𝙏𝙤 𝙂𝙚𝙩 𝙔𝙤𝙪𝙧 𝙈𝙤𝙫𝙞𝙚 😉", reply_markup=reply_markup)
        return

    elif data.split("_", 1)[0] == "sendall":
        ids = data.replace('sendall_', '')
        idstring = await find_all_file(ids)
        if not idstring:
            return await message.reply_text("<b>Something went wrong !</b>")
        idstring = idstring['name']
        fileids = idstring.split("L_I_N_K")

        for file_id in fileids:
            files_ = await get_file_details(file_id)

            if not files_:
                continue
            files = files_[0]
            title = files.file_name
            size = get_size(files.file_size)
            f_caption = files.caption
            k = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                caption=f_caption,
            )
        return

    elif data.split("_", 1)[0] == "cms":
        ids = data.replace('cms_', '')
        file_id, chat_id = ids.split("x_y_z")
        verify = await find_verify_user(message.from_user.id)
        now = datetime.datetime.now()
        time_now = int(now.timestamp())
        
        if not verify:
            url = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=uvew_{time_now}x_y_z{file_id}", chat_id)
            button = [[
                InlineKeyboardButton("Click Here To Verify ✅",
                                     url=url)
            ]]
            reply_markup = InlineKeyboardMarkup(button)
            return await emo.edit_text(text="𝘾𝙡𝙞𝙘𝙠 𝘽𝙚𝙡𝙤𝙬 𝙇𝙞𝙣𝙠 𝙊𝙣𝙘𝙚 𝘼𝙣𝙙 𝙀𝙣𝙟𝙤𝙮 𝙊𝙪𝙧 𝘽𝙤𝙩 𝙒𝙞𝙩𝙝𝙤𝙪𝙩 𝙇𝙞𝙣𝙠 𝙁𝙤𝙧 12 𝙃𝙤𝙪𝙧𝙨 😊👇", reply_markup=reply_markup)

        elif time_now - int(verify['time']) > 60*60*12:
            url = await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=uvew_{time_now}x_y_z{file_id}", chat_id)
            button = [[
                InlineKeyboardButton("Click Here To Verify ✅",
                                     url=url)
            ]]
            reply_markup = InlineKeyboardMarkup(button)
            return await emo.edit_text(text="𝘾𝙡𝙞𝙘𝙠 𝘽𝙚𝙡𝙤𝙬 𝙇𝙞𝙣𝙠 𝙊𝙣𝙘𝙚 𝘼𝙣𝙙 𝙀𝙣𝙟𝙤𝙮 𝙊𝙪𝙧 𝘽𝙤𝙩 𝙒𝙞𝙩𝙝𝙤𝙪𝙩 𝙇𝙞𝙣𝙠 𝙁𝙤𝙧 12 𝙃𝙤𝙪𝙧𝙨 😊👇", reply_markup=reply_markup)

        files_ = await get_file_details(file_id)
        if not files_:
            verify = await find_verify_user(message.from_user.id)
            now = datetime.datetime.now()
            time_now = int(now.timestamp())
            
            pre, file_id = ((base64.urlsafe_b64decode(
                data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
            try:

                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    protect_content=True if pre == 'filep' else False,
                )
                filetype = msg.media
                file = getattr(msg, filetype.value)
                title = file.file_name
                size = get_size(file.file_size)
                f_caption = f"<code>{title}</code>"
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption = CUSTOM_FILE_CAPTION.format(
                            file_name='' if title is None else title, file_size='' if size is None else size, file_caption='')
                    except:
                        return
                await msg.edit_caption(f_caption)
                return
            except:
                pass
            return await message.reply('No such file exist.')

        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(
                    file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if pre == 'filep' else False,
        )
        return
    
    if data.split("_", 1)[0] == "files":
        file_id = data.replace('files_', '')

    files_ = await get_file_details(file_id)
    if not files_:
        pre, file_id = ((base64.urlsafe_b64decode(
            data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
        try:
            """
            if not await check_verification(client, message.from_user.id):
                btn = [[
                    InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
                ]]
                await message.reply_text(
                    text="<b>You are not verified !\nKindly verify to continue !</b>",
                    reply_markup=InlineKeyboardMarkup(btn)
                )
                return"""

            msg = await client.send_cached_media(
                chat_id=message.from_user.id,
                file_id=file_id,
                protect_content=True if pre == 'filep' else False,
            )
            filetype = msg.media
            file = getattr(msg, filetype.value)
            title = file.file_name
            size = get_size(file.file_size)
            f_caption = f"<code>{title}</code>"
            if CUSTOM_FILE_CAPTION:
                try:
                    f_caption = CUSTOM_FILE_CAPTION.format(
                        file_name='' if title is None else title, file_size='' if size is None else size, file_caption='')
                except:
                    return
            await msg.edit_caption(f_caption)
            return
        except:
            pass
        return await message.reply('No such file exist.')

    files = files_[0]
    title = files.file_name
    size = get_size(files.file_size)
    f_caption = files.caption
    if CUSTOM_FILE_CAPTION:
        try:
            f_caption = CUSTOM_FILE_CAPTION.format(
                file_name='' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
        except Exception as e:
            logger.exception(e)
            f_caption = f_caption
    if f_caption is None:
        f_caption = f"{files.file_name}"
    """
        if not await check_verification(client, message.from_user.id):
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    """
    await client.send_cached_media(
        chat_id=message.from_user.id,
        file_id=file_id,
        caption=f_caption,
        protect_content=True if pre == 'filep' else False,
    )


# -------------------» ᴄʜᴀɴɴᴇʟ «-------------------- #

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):

    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **ɪɴᴅᴇxᴇᴅ ᴄʜᴀɴɴᴇʟs/ɢʀᴏᴜᴘs**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**ᴛᴏᴛᴀʟ:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


# -------------------» ʟᴏɢs «-------------------- #

@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))


# -------------------» ᴅᴇʟᴇᴛᴇ «-------------------- #

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("ᴅᴇʟᴇᴛɪɴɢ....🗑️", quote=True)
    else:
        await message.reply('ʀᴇᴘʟʏ ᴛᴏ ғɪʟᴇ ᴡɪᴛʜ /delete ᴡʜɪᴄʜ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴅᴇʟᴇᴛᴇ.', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('ᴛʜɪs ɪs ɴᴏᴛ sᴜᴘᴘᴏʀᴛᴇᴅ ғɪʟᴇ ғᴏʀᴍᴀᴛ.')
        return

    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('**ғɪʟᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ.**')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
        })
        if result.deleted_count:
            await msg.edit('**ғɪʟᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ.**')
        else:

            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('**ғɪʟᴇ sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ.**')
            else:
                await msg.edit('ғɪʟᴇ ɴᴏᴛ ғᴏᴜɴᴅ ɪɴ ᴅᴀᴛᴀʙᴀsᴇ.')


# -------------------» ᴅᴇʟᴇᴛᴇ-ᴀʟʟ «-------------------- #

@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        '**𝚃𝙷𝙸𝚂 𝙿𝚁𝙾𝙲𝙴𝚂𝚂 𝚆𝙸𝙻𝙻 𝙳𝙴𝙻𝙴𝚃𝙴 𝙰𝙻𝙻 𝚃𝙷𝙴 𝙵𝙸𝙻𝙴𝚂 𝙵𝚁𝙾𝙼 𝚈𝙾𝚄𝚁 𝙳𝙰𝚃𝙰𝙱𝙰𝚂𝙴.\n𝙳𝙾 𝚈𝙾𝚄 𝚆𝙰𝙽𝚃 𝚃𝙾 𝙲𝙾𝙽𝚃𝙸𝙽𝚄𝙴 𝚃𝙷𝙸𝚂..??**',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="⚡ ʏᴇs ⚡", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="❄ ᴄᴀɴᴄᴇʟ ❄", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


# -------------------» ʀᴇɢᴇx-ᴄᴀʟʟʙᴀᴄᴋ «-------------------- #

@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')
    await message.message.edit('sᴜᴄᴄᴇssғᴜʟʟʏ ᴅᴇʟᴇᴛᴇᴅ ᴀʟʟ ғɪʟᴇs ᴛʜᴇ ɪɴᴅᴇxᴇᴅ ғɪʟᴇs.')


# -------------------» sᴇᴛᴛɪɴɢ «-------------------- #

@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !!", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    settings = await db.get_settings(grp_id)
    
    if not 'enable_shortlink' in settings.keys():
        await save_group_settings(grpid, 'enable_shortlink', ENABLE_SHORTLINK)
        
    settings = await db.get_settings(grp_id)    

    if settings is not None:
        buttons = [
            [
                InlineKeyboardButton(
                    'ғɪʟᴛᴇʀ ʙᴜᴛᴛᴏɴ',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'sɪɴɢʟᴇ' if settings["button"] else '𝐃𝐎𝐔𝐁𝐋𝐄',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ʙᴏᴛ ᴘᴍ',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ ʏᴇs' if settings["botpm"] else '❌ 𝐍𝐎',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ғɪʟᴇ sᴇᴄᴜʀᴇ',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ ʏᴇs' if settings["file_secure"] else '❌ 𝐍𝐎',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'sᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ ʏᴇs' if settings["spell_check"] else '❌ 𝐍𝐎',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴡᴇʟᴄᴏᴍᴇ',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ ʏᴇs' if settings["welcome"] else '❌ 𝐍𝐎',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'sʜᴏʀᴛʟɪɴᴋ',
                    callback_data=f'setgs#shortlink#{grp_id}',
                ),
                InlineKeyboardButton(
                    f'✅ {settings["shortlink"]}' if settings["shortlink"] else SHORTLINK_URL,
                    callback_data=f'setgs#shortlink#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'sʜᴏʀᴛʟɪɴᴋ ᴀᴘɪ',
                    callback_data=f'setgs#shortlink_api#{grp_id}',
                ),
                InlineKeyboardButton(
                    f'✅ {settings["shortlink_api"][:10]}...' if settings["shortlink_api"] else SHORTLINK_API[:10] + '...',
                    callback_data=f'setgs#shortlink_api#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ғᴏʀᴄᴇ sᴜʙ',
                    callback_data=f'setgs#forcesub#{grp_id}',
                ),
                InlineKeyboardButton(
                    f'✅ {settings["forcesub"]}...' if 'forcesub' in settings else 'Not Set',
                    callback_data=f'setgs#forcesub#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ',
                    callback_data=f'setgs#tutorial#{grp_id}',
                ),
                InlineKeyboardButton(
                    f'✅ {settings["tutorial"]}...' if 'tutorial' in settings else 'Not Set',
                    callback_data=f'setgs#tutorial#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'SʜᴏʀᴛLɪɴᴋ',
                    callback_data=f'setgs#enable_shortlink#{settings["enable_shortlink"]}#{grp_id}'),
                InlineKeyboardButton('✅ ʏᴇs' if settings["enable_shortlink"] else '❌ 𝐍𝐎',
                    callback_data=f'setgs#enable_shortlink#{settings["enable_shortlink"]}#{grp_id}')
            ]
        ]
        print(settings)

        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_text(
            text=f"<b>ᴄʜᴀɴɢᴇ ᴛʜᴇ ʙᴏᴛ sᴇᴛᴛɪɴɢ ғᴏʀ {title}..⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode=enums.ParseMode.HTML,
            reply_to_message_id=message.id
        )


# -------------------» sᴇᴛ-ᴛᴜᴛᴏʀɪᴀʟ «-------------------- #

@Client.on_message(filters.command('set_tutorial'))
async def tutorial_cmd(bot, message):
    grpid = None
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await bot.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ", quote=True)

    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grp_id, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅs !</b>")
    try:
        command, tutorial = data.split(" ")
    except ValueError:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ :(\n\nᴜsᴇ ᴘʀᴏᴘᴇʀ ғᴏʀᴍᴀᴛ !\n\nғᴏʀᴍᴀᴛ:\n\n<code>/set_tutorial LINK</code></b>")

    reply = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grp_id, 'tutorial', tutorial)
    await reply.edit(f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘɢʀᴀᴅᴇᴅ ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ ғᴏʀ {title} ᴛᴏ\n\n{tutorial}. \nᴜsᴇ /del_tutorial ᴛᴏ ʀᴇᴍᴏᴠᴇ ɪᴛ.")


# -------------------» ᴅᴇʟ-ᴛᴜᴛᴏʀɪᴀʟ «-------------------- #

@Client.on_message(filters.command('del_tutorial'))
async def del_tutorial_cmd(bot, message):
    grpid = None
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await bot.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ.", quote=True)

    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grp_id, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !</b>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grp_id, 'tutorial', 'https://t.me/')
    await reply.edit(f"sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇ ʏᴏᴜʀ ᴛᴜᴛᴏʀɪᴀʟ ʟɪɴᴋ.")


# -------------------» sᴇᴛ-ғᴏʀᴄᴇ-sᴜʙ «-------------------- #

@Client.on_message(filters.command('forcesub'))
async def forcesub_cmd(bot, message):
    grpid = None
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await bot.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ", quote=True)

    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grp_id, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !</b>")
    try:
        command, forcesub = data.split(" ")
    except ValueError:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ :(\n\nᴜsᴇ ᴘʀᴏᴘᴇʀ ғᴏʀᴍᴀᴛ !\n\nғᴏʀᴍᴀᴛ:\n\n<code>/forcesub CHANNEL_ID or GROUP_ID</code></b>")

    reply = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grp_id, 'forcesub', forcesub)
    await reply.edit(f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘɢʀᴀᴅᴇᴅ ʏᴏᴜʀ ғᴏʀᴄᴇ sᴜʙ ғᴏʀ {title} ᴛᴏ\n\n{forcesub}")


# -------------------» ᴅᴇʟ-ғᴏʀᴄᴇ-sᴜʙ «-------------------- #

@Client.on_message(filters.command('del_forcesub'))
async def del_forcesub_cmd(bot, message):
    grpid = None
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await bot.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ", quote=True)

    userid = message.from_user.id
    user = await bot.get_chat_member(grp_id, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄᴏɴᴍᴀɴᴅ !</b>")
    reply = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grp_id, 'forcesub', AUTH_CHANNEL)
    await reply.edit(f"sᴜᴄᴄᴇssғᴜʟʟʏ ʀᴇᴍᴏᴠᴇᴅ ʏᴏᴜʀ ғᴏʀᴄᴇ.")


# -------------------» sᴇᴛ-ᴛᴇᴍᴘʟᴀᴛᴇ «-------------------- #

@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("**𝙲𝙷𝙴𝙲𝙺𝙸𝙽𝙶 𝙽𝙴𝚆 𝚃𝙴𝙼𝙿𝙻𝙰𝚃𝙴**")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != enums.ChatMemberStatus.ADMINISTRATOR
            and st.status != enums.ChatMemberStatus.OWNER
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴜᴘɢʀᴀᴅᴇᴅ ʏᴏᴜʀ ᴛᴇᴍᴘʟᴀᴛᴇ ғᴏʀ {title} to\n\n{template}")


# -------------------» sᴇᴛ-sʜᴏʀᴛʟɪɴᴋ «-------------------- #

@Client.on_message(filters.command('shortlink'))
async def shortlink(bot, message):
    grpid = None
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")

    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await bot.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!", quote=True)
                return
        else:
            await message.reply_text("ɪ'ᴍ ɴᴏᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴀɴʏ ɢʀᴏᴜᴘs !", quote=True)
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return await message.reply_text("sᴏᴍᴇᴛʜɪɴɢ ᴡᴇɴᴛ ᴡʀᴏɴɢ", quote=True)

    data = message.text
    userid = message.from_user.id
    user = await bot.get_chat_member(grp_id, userid)
    if user.status != enums.ChatMemberStatus.ADMINISTRATOR and user.status != enums.ChatMemberStatus.OWNER and str(userid) not in ADMINS:
        return await message.reply_text("<b>ʏᴏᴜ ᴅᴏɴᴛ ʜᴀᴠᴇ ᴀᴄᴄᴇss ᴛᴏ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ !</b>")
    try:
        command, shorlink_url, api = data.split(" ")
    except ValueError:
        return await message.reply_text(f"<b>ʜᴇʏ {message.from_user.mention}, ᴄᴏᴍᴍᴀɴᴅ ɪɴᴄᴏᴍᴘʟᴇᴛᴇ :(\n\nᴜsᴇ ᴘʀᴏᴘᴇʀ ғᴏʀᴍᴀᴛ !\n\nғᴏʀᴍᴀᴛ:\n\n<code>/shortlink mdisk.link b6d97f6s96ds69d69d68d575d</code></b>")

    reply = await message.reply_text("<b>ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ...</b>")
    await save_group_settings(grp_id, 'shortlink', shorlink_url)
    await save_group_settings(grp_id, 'shortlink_api', api)
    await reply.edit_text(f"<b>sᴜᴄᴄᴇssғᴜʟʟʏ ᴀᴅᴅᴇᴅ sʜᴏʀᴛʟɪɴᴋ ᴀᴘɪ ғᴏʀ {title}\n\nᴄᴜʀʀᴇɴᴛ sʜɪʀᴛʟɪɴᴋ ᴡᴇʙsɪᴛᴇ : <code>{shorlink_url}</code>\nᴄᴜʀʀᴇɴᴛ ᴀᴘɪ : <code>{api}</code>.</b>")
                  

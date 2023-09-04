import asyncio
import re
import ast
import math
import time
from Movies.database.quickdb import add_all_file
from Movies.utils import get_shortlink, get_token, check_verification, get_verify_shorted_link
from pyrogram.errors.exceptions.bad_request_400 import MediaEmpty, PhotoInvalidDimensions, WebpageMediaEmpty
from script import script
import pyrogram
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
import pytz
from Movies.database.connections import active_connection, all_connections, delete_connection, if_active, make_active, \
    make_inactive
from config import *
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, filters, enums
from pyrogram.errors import ChatAdminRequired, FloodWait, UserIsBlocked, MessageNotModified, PeerIdInvalid
from Movies.utils import get_size, is_subscribed, get_poster, search_gagala, temp, get_settings, save_group_settings, replace_username, remove_words, remove_words2
from Movies.database.chats import db
from Movies.database.media import Media, get_file_details, get_search_results
from Movies.database.filters import (
    del_all,
    find_filter,
    get_filters,
)
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)

BUTTONS = {}
SPELL_CHECK = {}
FILTER_MODE = {}
KEYWORD = {}

# ------------------------------------------------------------------------------------------------- #


@Client.on_message(filters.command('autofilter'))
async def fil_mod(client, message):
    mode_on = ["yes", "on", "true"]
    mode_of = ["no", "off", "false"]

    try:
        args = message.text.split(None, 1)[1].lower()
    except:
        return await message.reply("**𝙸𝙽𝙲𝙾𝙼𝙿𝙻𝙴𝚃𝙴 𝙲𝙾𝙼𝙼𝙰𝙽𝙳...**")

    m = await message.reply("**𝚂𝙴𝚃𝚃𝙸𝙽𝙶.../**")

    if args in mode_on:
        FILTER_MODE[str(message.chat.id)] = "True"
        await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙴𝙽𝙰𝙱𝙻𝙴𝙳**")

    elif args in mode_of:
        FILTER_MODE[str(message.chat.id)] = "False"
        await m.edit("**𝙰𝚄𝚃𝙾𝙵𝙸𝙻𝚃𝙴𝚁 𝙳𝙸𝚂𝙰𝙱𝙻𝙴𝙳**")
    else:
        await m.edit("USE :- /autofilter on 𝙾𝚁 /autofilter off")
# ------------------------------------------------------------------------------------------------- #

# ------------------------------------------------------------------------------------------------- #

@Client.on_message(filters.text & filters.incoming)
async def give_filter(client, message):
    """
    chat_type = message.chat.type
    if not await check_verification(client, message.from_user.id) and chat_type == enums.ChatType.PRIVATE:
        btn = [[
            InlineKeyboardButton("Verify", url=await get_token(client, message.from_user.id, f"https://telegram.me/{temp.U_NAME}?start="))
        ]]
        await message.reply_text(
            text="<b>You are not verified !\nKindly verify to continue !</b>",
            reply_markup=InlineKeyboardMarkup(btn)
        )
        return
    """
    if message.chat is None or message.from_user is None:
        return
    k = await manual_filters(client, message)
    if k == False:
        await auto_filter(client, message)

# ------------------------------------------------------------------------------------------------- #

@Client.on_callback_query(filters.regex(r"^next"))
async def next_page(bot, query):
    ident, req, key, offset = query.data.split("_")
    if int(req) not in [query.from_user.id, 0]:
        return await query.answer("oKda", show_alert=True)
    try:
        offset = int(offset)
    except:
        offset = 0
    search = BUTTONS.get(key)
    if not search:
        await query.answer("You are using one of my old messages, please send the request again.", show_alert=True)
        return

    files, n_offset, total = await get_search_results(search, offset=offset, filter=True)
    try:
        n_offset = int(n_offset)
    except:
        n_offset = 0

    if not files:
        return
    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    settings = await get_settings(query.message.chat.id)

    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)
    await add_all_file(dbid, fileids)

    btn = [[
        InlineKeyboardButton(
            text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
            callback_data=f"uvew_{file.file_id}"
        ),
        InlineKeyboardButton(
            text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
            callback_data=f"uvew_{file.file_id}"
        )][:settings["button"]]
        for file in files
    ]
   #btn.insert(0,
   #            [
   #                InlineKeyboardButton(
   #                    f"๏ sᴇɴᴅ ᴀʟʟ ғɪʟᴇ ๏", url=await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=sendall_{dbid}", query.message.chat.id))
   #            ]
   #            )

    if 0 < offset <= 10:
        off_set = 0
    elif offset == 0:
        off_set = None
    else:
        off_set = offset - 10
    if n_offset == 0:
        btn.append(
            [InlineKeyboardButton("⏪ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
             InlineKeyboardButton(f"📃 ᴘᴀɢᴇs {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}",
                                  callback_data="pages")]
        )
    elif off_set is None:
        btn.append(
            [InlineKeyboardButton(f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
             InlineKeyboardButton("ɴᴇxᴛ ➡️", callback_data=f"next_{req}_{key}_{n_offset}")])
    else:
        btn.append(
            [
                InlineKeyboardButton(
                    "⏪ ʙᴀᴄᴋ", callback_data=f"next_{req}_{key}_{off_set}"),
                InlineKeyboardButton(
                    f"🗓 {math.ceil(int(offset) / 10) + 1} / {math.ceil(total / 10)}", callback_data="pages"),
                InlineKeyboardButton(
                    "ɴᴇxᴛ ➡️", callback_data=f"next_{req}_{key}_{n_offset}")
            ],
        )
        
    btn.insert(0, [
        InlineKeyboardButton("! Sᴇʟᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ !", callback_data=f"select_lang#{query.from_user.id}#{key}")
    ])    
    
    btn.insert(0, [
        InlineKeyboardButton("✅ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ✅",
                             url=settings["tutorial"] if "tutorial" in settings else 'https://t.me/okhajaj/8')
    ])
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()
    
# https://telegram.dog/premiumbotz
@Client.on_callback_query(filters.regex(r"^lang"))
async def language_check(bot, query):
    _, userid, language, key = query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if language == "unknown":
        return await query.answer("Sᴇʟᴇᴄᴛ ᴀɴʏ ʟᴀɴɢᴜᴀɢᴇ ғʀᴏᴍ ᴛʜᴇ ʙᴇʟᴏᴡ ʙᴜᴛᴛᴏɴs !", show_alert=True)
    movie = KEYWORD.get(key)
    KEYWORD[key] = movie
    if not movie:
        return await query.answer(script.OLD_ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    if language != "home":
        movie = f"{movie} {language}"
    files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
    if files:
        settings = await get_settings(query.message.chat.id)
        fileids = [file.file_id for file in files]
        dbid = fileids[0]
        fileids = "L_I_N_K".join(fileids)
        await add_all_file(dbid, fileids)
    
        btn = [[
            InlineKeyboardButton(
                text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
                callback_data=f"uvew_{file.file_id}"
            ),
            InlineKeyboardButton(
                text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
                callback_data=f"uvew_{file.file_id}"
            )][:settings["button"]]
            for file in files
        ]
        #btn.insert(0,
        #           [
        #               InlineKeyboardButton(
        #                   f"๏ sᴇɴᴅ ᴀʟʟ ғɪʟᴇ ๏", url=await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=sendall_{dbid}", message.chat.id))
        #           ]
        #           )
        
        btn.insert(0, [
            InlineKeyboardButton("! Sᴇʟᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ !", callback_data=f"select_lang#{query.from_user.id}#{key}")
        ])    
    
        btn.insert(0, [
            InlineKeyboardButton("✅ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ✅",
                                 url=settings["tutorial"] if "tutorial" in settings else 'https://t.me/Waiting_Area12')
        ])
    
        if offset != "":
            key = f"{query.message.chat.id}-{query.message.id}"
            BUTTONS[key] = movie 
            req = query.from_user.id if query.from_user else 0
            btn.append(
                [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
                 InlineKeyboardButton(text="ɴᴇxᴛ ⏩", callback_data=f"next_{req}_{key}_{offset}")]
            )
        else:
            btn.append(
                [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
            )
        try:
            await query.edit_message_reply_markup(
                reply_markup=InlineKeyboardMarkup(btn)
            )
        except MessageNotModified:
            pass
        await query.answer()
    else:
        return await query.answer(f"Sᴏʀʀʏ, Nᴏ ғɪʟᴇs ғᴏᴜɴᴅ ғᴏʀ ʏᴏᴜʀ ᴏ̨ᴜᴇʀʏ {movie}.", show_alert=True)
        
# https://telegram.dog/premiumbotz    
@Client.on_callback_query(filters.regex(r"^select_lang"))
async def select_language(bot, query):
    _, userid, key = query.data.split("#")
    if int(userid) not in [query.from_user.id, 0]:
        return await query.answer(script.ALRT_TXT.format(query.from_user.first_name), show_alert=True)
    btn = [[
        InlineKeyboardButton("Sᴇʟᴇᴄᴛ Yᴏᴜʀ Dᴇꜱɪʀᴇᴅ Lᴀɴɢᴜᴀɢᴇ ↓", callback_data=f"lang#{userid}#unknown#{key}")
    ],[
        InlineKeyboardButton("Eɴɢʟɪꜱʜ", callback_data=f"lang#{userid}#eng#{key}"),
        InlineKeyboardButton("Tᴀᴍɪʟ", callback_data=f"lang#{userid}#tam#{key}"),
        InlineKeyboardButton("Hɪɴᴅɪ", callback_data=f"lang#{userid}#hin#{key}")
    ],[
        InlineKeyboardButton("Kᴀɴɴᴀᴅᴀ", callback_data=f"lang#{userid}#kan#{key}"),
        InlineKeyboardButton("Tᴇʟᴜɢᴜ", callback_data=f"lang#{userid}#tel#{key}")
    ],[
        InlineKeyboardButton("Mᴀʟᴀʏᴀʟᴀᴍ", callback_data=f"lang#{userid}#mal#{key}")
    ],[
        InlineKeyboardButton("Mᴜʟᴛɪ Aᴜᴅɪᴏ", callback_data=f"lang#{userid}#multi#{key}"),
        InlineKeyboardButton("Dᴜᴀʟ Aᴜᴅɪᴏ", callback_data=f"lang#{userid}#dual#{key}")
    ],[
        InlineKeyboardButton("Gᴏ Bᴀᴄᴋ", callback_data=f"lang#{userid}#home#{key}")
    ]]
    try:
        await query.edit_message_reply_markup(
            reply_markup=InlineKeyboardMarkup(btn)
        )
    except MessageNotModified:
        pass
    await query.answer()


# ------------------------------------------------------------------------------------------------- #

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "close_data":
        await query.message.delete()
    elif query.data == "delallconfirm":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            grpid = await active_connection(str(userid))
            if grpid is not None:
                grp_id = grpid
                try:
                    chat = await client.get_chat(grpid)
                    title = chat.title
                except:
                    await query.message.edit_text("Make sure I'm present in your group!!", quote=True)
                    return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')
            else:
                await query.message.edit_text(
                    "I'm not connected to any groups!\nCheck /connections or connect to any groups",
                    quote=True
                )
                return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            title = query.message.chat.title

        else:
            return await query.answer('@OkFilterBot Is Best')

        st = await client.get_chat_member(grp_id, userid)
        if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
            await del_all(query.message, grp_id, title)
        else:
            await query.answer("You need to be Group Owner or an Auth User to do that!", show_alert=True)


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "delallcancel":
        userid = query.from_user.id
        chat_type = query.message.chat.type

        if chat_type == enums.ChatType.PRIVATE:
            await query.message.reply_to_message.delete()
            await query.message.delete()

        elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
            grp_id = query.message.chat.id
            st = await client.get_chat_member(grp_id, userid)
            if (st.status == enums.ChatMemberStatus.OWNER) or (str(userid) in ADMINS):
                await query.message.delete()
                try:
                    await query.message.reply_to_message.delete()
                except:
                    pass
            else:
                await query.answer("Buddy Don't Touch Others Property 😁", show_alert=True)


# ------------------------------------------------------------------------------------------------- #

    elif "groupcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        act = query.data.split(":")[2]
        hr = await client.get_chat(int(group_id))
        title = hr.title
        user_id = query.from_user.id

        if act == "":
            stat = "𝙲𝙾𝙽𝙽𝙴𝙲𝚃"
            cb = "connectcb"
        else:
            stat = "𝙳𝙸𝚂𝙲𝙾𝙽𝙽𝙴𝙲𝚃"
            cb = "disconnect"

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"{stat}", callback_data=f"{cb}:{group_id}"),
             InlineKeyboardButton("𝙳𝙴𝙻𝙴𝚃𝙴", callback_data=f"deletecb:{group_id}")],
            [InlineKeyboardButton("𝙱𝙰𝙲𝙺", callback_data="backcb")]
        ])

        await query.message.edit_text(
            f"𝙶𝚁𝙾𝚄𝙿 𝙽𝙰𝙼𝙴 :- **{title}**\n𝙶𝚁𝙾𝚄𝙿 𝙸𝙳 :- `{group_id}`",
            reply_markup=keyboard,
            parse_mode=enums.ParseMode.MARKDOWN
        )
        return await query.answer('Piracy Is Crime')


# ------------------------------------------------------------------------------------------------- #

    elif "connectcb" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title

        user_id = query.from_user.id

        mkact = await make_active(str(user_id), str(group_id))

        if mkact:
            await query.message.edit_text(
                f"𝙲𝙾𝙽𝙽𝙴𝙲𝚃𝙴𝙳 𝚃𝙾 **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text('Some error occurred!!', parse_mode=enums.ParseMode.MARKDOWN)
        return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')


# ------------------------------------------------------------------------------------------------- #

    elif "disconnect" in query.data:
        await query.answer()

        group_id = query.data.split(":")[1]

        hr = await client.get_chat(int(group_id))

        title = hr.title
        user_id = query.from_user.id

        mkinact = await make_inactive(str(user_id))

        if mkinact:
            await query.message.edit_text(
                f"𝙳𝙸𝚂𝙲𝙾𝙽𝙽𝙴𝙲𝚃 FROM **{title}**",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')


# ------------------------------------------------------------------------------------------------- #

    elif "deletecb" in query.data:
        await query.answer()

        user_id = query.from_user.id
        group_id = query.data.split(":")[1]

        delcon = await delete_connection(str(user_id), str(group_id))

        if delcon:
            await query.message.edit_text(
                "Successfully deleted connection"
            )
        else:
            await query.message.edit_text(
                f"Some error occurred!!",
                parse_mode=enums.ParseMode.MARKDOWN
            )
        return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "backcb":
        await query.answer()

        userid = query.from_user.id

        groupids = await all_connections(str(userid))
        if groupids is None:
            await query.message.edit_text(
                "There are no active connections!! Connect to some groups first.",
            )
            return await query.answer('𝙿𝙻𝙴𝙰𝚂𝙴 𝚂𝙷𝙰𝚁𝙴 𝙰𝙽𝙳 𝚂𝚄𝙿𝙿𝙾𝚁𝚃')
        buttons = []
        for groupid in groupids:
            try:
                ttl = await client.get_chat(int(groupid))
                title = ttl.title
                active = await if_active(str(userid), str(groupid))
                act = " - ACTIVE" if active else ""
                buttons.append(
                    [
                        InlineKeyboardButton(
                            text=f"{title}{act}", callback_data=f"groupcb:{groupid}:{act}"
                        )
                    ]
                )
            except:
                pass
        if buttons:
            await query.message.edit_text(
                "Your connected group details ;\n\n",
                reply_markup=InlineKeyboardMarkup(buttons)
            )


# ------------------------------------------------------------------------------------------------- #

    elif "alertmessage" in query.data:
        grp_id = query.message.chat.id
        i = query.data.split(":")[1]
        keyword = query.data.split(":")[2]
        reply_text, btn, alerts, fileid = await find_filter(grp_id, keyword)
        if alerts is not None:
            alerts = ast.literal_eval(alerts)
            alert = alerts[int(i)]
            alert = alert.replace("\\n", "\n").replace("\\t", "\t")
            await query.answer(alert, show_alert=True)


# ------------------------------------------------------------------------------------------------- #

    elif query.data.startswith("file"):
        ident, file_id = query.data.split("#")
        files_ = await get_file_details(file_id)
        if not files_:
            return await query.answer('No such file exist.')
        files = files_[0]
        title = files.file_name
        size = get_size(files.file_size)
        f_caption = files.caption
        settings = await get_settings(query.message.chat.id)
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
                                                       file_size='' if size is None else size,
                                                       file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
            f_caption = f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"

        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            elif settings['botpm']:
                await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
                return
            else:
                await client.send_cached_media(
                    chat_id=query.from_user.id,
                    file_id=file_id,
                    caption=f_caption,
                    protect_content=True if ident == "filep" else False
                )
                await query.answer('Check PM, I have sent files in pm', show_alert=True)
        except UserIsBlocked:
            await query.answer('You Are Blocked to use me !', show_alert=True)
        except PeerIdInvalid:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")
        except Exception as e:
            await query.answer(url=f"https://t.me/{temp.U_NAME}?start={ident}_{file_id}")


# ------------------------------------------------------------------------------------------------- #

    elif query.data.startswith("uvew"):
        file_id = query.data.replace('uvew_', '')
        url = f"t.me/{temp.U_NAME}?start=cms_{file_id}x_y_z{query.message.chat.id}"
        button = [[
            InlineKeyboardButton("Click Here To Download ✅",
                                 url=url)
        ]]        
        reply_markup = InlineKeyboardMarkup(button)
        pmLink = f"t.me/{temp.U_NAME}?start=cms_{file_id}x_y_z{query.message.chat.id}"
        settings = await get_settings(query.message.chat.id)
        try:
            if AUTH_CHANNEL and not await is_subscribed(client, query):
                await query.answer(url=pmLink)
                return
            elif settings['botpm']:
                await query.answer(url=pmLink)
                return
            else:
                await client.send_message(
                    chat_id=query.from_user.id,
                    text='click the bellow button to get movie',
                    reply_markup=reply_markup
                )
                await query.answer(f'Check PM, I have sent link : {url} in pm', show_alert=True)
        except UserIsBlocked:
            await query.answer('You Are Blocked to use me !', show_alert=True)
        except PeerIdInvalid:
            await query.answer('Invalid Id !', show_alert=True)
        except Exception as e:
            await query.answer('Something went wrong :()', show_alert=True)
            logger.exception(e)

# ------------------------------------------------------------------------------------------------- #

    # elif query.data.startswith("checksub"):
    #     if AUTH_CHANNEL and not await is_subscribed(client, query):
    #         await query.answer("ᴊᴏɪɴ ᴏᴜʀ ʙᴀᴄᴋ-ᴜᴘ ᴄʜᴀɴɴᴇʟ ᴍᴀʜɴ! 😒", show_alert=True)
    #         return
    #     ident, file_id = query.data.split("#")
    #     if file_id == "send_all":
    #         send_files = temp.SEND_ALL_TEMP.get(query.from_user.id)
    #         is_over = await send_all(client, query.from_user.id, send_files, ident)
    #         if is_over == 'done':
    #             return await query.answer(f"ʜᴇʏ {query.from_user.first_name}, ᴀʟʟ ғɪʟᴇs ᴏɴ ᴛʜɪs ᴘᴀɢᴇ ʜᴀs ʙᴇᴇɴ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ ᴛᴏ ʏᴏᴜʀ ᴘᴍ !", show_alert=True)
    #         elif is_over == 'fsub':
    #             return await query.answer("ʜᴇʏ, ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴊᴏɪɴᴇᴅ ɪɴ ᴍʏ ʙᴀᴄᴋ ᴜᴘ ᴄʜᴀɴɴᴇʟ. ᴄʜᴇᴄᴋ ᴍʏ ᴘᴍ ᴛᴏ ᴊᴏɪɴ ᴀɴᴅ ɢᴇᴛ ғɪʟᴇs !", show_alert=True)

    #     files_ = await get_file_details(file_id)
    #     if not files_:
    #         return await query.answer('Nᴏ sᴜᴄʜ ғɪʟᴇ ᴇxɪsᴛ.')
    #     files = files_[0]
    #     title = files.file_name
    #     size = get_size(files.file_size)
    #     f_caption = files.caption
    #     if CUSTOM_FILE_CAPTION:
    #         try:
    #             f_caption = CUSTOM_FILE_CAPTION.format(file_name='' if title is None else title,
    #                                                    file_size='' if size is None else size,
    #                                                    file_caption='' if f_caption is None else f_caption)
    #         except Exception as e:
    #             logger.exception(e)
    #             f_caption = f_caption
    #     if f_caption is None:
    #         f_caption = f"{title}"
    #     await query.answer()

    #     await client.send_cached_media(
    #         chat_id=query.from_user.id,
    #         file_id=file_id,
    #         caption=f_caption,
    #         protect_content=True if ident == 'checksubp' else False,
    #         reply_markup=InlineKeyboardMarkup(
    #             [
    #                 [
    #                     InlineKeyboardButton("test", url="t.me/AnonDEveloper")
    #                 ]
    #             ]
    #         )
    #     )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "pages":
        await query.answer()

# ------------------------------------------------------------------------------------------------- #

    elif query.data == "start":
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
                '💸 ᴄᴏɴɴᴇᴄᴛ ʏᴏᴜʀ sʜᴏʀᴛʟɪɴᴋ ғʀᴇᴇ 💸', url='https://t.me/joinnowearn/82')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.START_TXT.format(
                query.from_user.mention, temp.U_NAME, temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "help":
        buttons = [[
            InlineKeyboardButton('ᴍᴀɴᴜᴀʟ ғɪʟᴛᴇʀ',
                                 callback_data='manuelfilter'),
            InlineKeyboardButton('ᴀᴜᴛᴏ ғɪʟᴛᴇʀ', callback_data='autofilter')
        ], [
            InlineKeyboardButton('ᴄᴏɴɴᴇᴄᴛɪᴏɴs', callback_data='coct'),
            InlineKeyboardButton('ᴇxᴛʀᴀ ᴍᴏᴅs', callback_data='extra')
        ], [
            InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.HELP_TXT.format(query.from_user.mention),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "about":
        buttons = [[
            InlineKeyboardButton('ʜᴏᴍᴇ', callback_data='start'),
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ABOUT_TXT.format(temp.B_NAME),
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "manuelfilter":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ʙᴜᴛᴛᴏɴs', callback_data='button')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.MANUELFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "button":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='manuelfilter')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.BUTTON_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "autofilter":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.AUTOFILTER_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "coct":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.CONNECTION_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "extra":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='help'),
            InlineKeyboardButton('ᴀᴅᴍɪɴ', callback_data='admin')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.EXTRAMOD_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data == "admin":
        buttons = [[
            InlineKeyboardButton('ʙᴀᴄᴋ', callback_data='extra')
        ]]
        reply_markup = InlineKeyboardMarkup(buttons)
        await query.message.edit_text(
            text=script.ADMIN_TXT,
            reply_markup=reply_markup,
            parse_mode=enums.ParseMode.HTML
        )


# ------------------------------------------------------------------------------------------------- #

    elif query.data.startswith("setgs"):
        ident, set_type, status, grp_id = query.data.split("#")
        grpid = await active_connection(str(query.from_user.id))

        if str(grp_id) != str(grpid):
            await query.message.edit("ʏᴏᴜʀ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴ ʜᴀs ʙᴇᴇɴ ᴄʜᴀɴɢᴇᴅ. ɢᴏ ᴛᴏ /settings.")
            return await query.answer('ᴘʟᴇᴀsᴇ sʜᴀʀᴇ ᴀɴᴅ sᴜᴘᴘᴏʀᴛ.')
            
        if set_type == "enable_shortlink" and query.from_user.id not in ADMINS:
            return await query.answer('Only Bot admins can change this settings.', show_alert=True)

        if status == "True":
            await save_group_settings(grpid, set_type, False)
        else:
            await save_group_settings(grpid, set_type, True)

        settings = await db.get_settings(grpid)
        
        if not 'enable_shortlink' in settings.keys():
            await save_group_settings(grpid, 'enable_shortlink', ENABLE_SHORTLINK)
            
        settings = await db.get_settings(grp_id)    

        if settings is not None:
            buttons = [
                [
                    InlineKeyboardButton('ғɪʟᴛᴇʀ ʙᴜᴛᴛᴏɴ',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}'),
                    InlineKeyboardButton('sɪɴɢʟᴇ' if settings["button"] else '𝐃𝐎𝐔𝐁𝐋𝐄',
                                         callback_data=f'setgs#button#{settings["button"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton(
                        'ʙᴏᴛ ᴘᴍ', callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ ʏᴇs' if settings["botpm"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#botpm#{settings["botpm"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('ғɪʟᴇ sᴇᴄᴜʀᴇ',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ ʏᴇs' if settings["file_secure"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#file_secure#{settings["file_secure"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton('sᴘᴇʟʟ ᴄʜᴇᴄᴋ',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ ʏᴇs' if settings["spell_check"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#spell_check#{settings["spell_check"]}#{str(grp_id)}')
                ],
                [
                    InlineKeyboardButton(
                        'ᴡᴇʟᴄᴏᴍᴇ', callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}'),
                    InlineKeyboardButton('✅ ʏᴇs' if settings["welcome"] else '❌ 𝐍𝐎',
                                         callback_data=f'setgs#welcome#{settings["welcome"]}#{str(grp_id)}')
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
            
            reply_markup = InlineKeyboardMarkup(buttons)
            await query.message.edit_reply_markup(reply_markup)
    await query.answer('ᴘʟᴇᴀsᴇ sʜᴀʀᴇ ᴀɴᴅ sᴜᴘᴘᴏʀᴛ')


# ------------------------------------------------------------------------------------------------- #

async def auto_filter(client, message):
    srh_msg = await message.reply_text(f"<b>Sᴇᴀʀᴄʜɪɴɢ...🔎</b>")
    settings = await db.get_settings(message.chat.id)
    if message.text.startswith("/"):
        return await srh_msg.delete()  # ignore commands
    if re.findall("((^\/|^,|^!|^\.|^[\U0001F600-\U000E007F]).*)", message.text):
        return
    if len(message.text) < 100:
        search = message.text
        files, offset, total_results = await get_search_results(search.lower(), offset=0, filter=True)
        if not files:
            re_search = remove_words(search)
            search = re_search
            files, offset, total_results = await get_search_results(re_search.lower(), offset=0, filter=True)
            if not files:
                re_search_ = re.sub(r'(?:{})'.format('|'.join(map(re.escape, WITHOUT_WORDS_IGNORE))), '', re_search)
                re_search_ = re_search_.replace("  ", " ")
                search = re_search_
                files, offset, total_results = await get_search_results(re_search_.lower(), offset=0, filter=True)
                if not files:
                    return await advantage_spell_chok(client, message, srh_msg)
    else:
        return await srh_msg.delete()

    fileids = [file.file_id for file in files]
    dbid = fileids[0]
    fileids = "L_I_N_K".join(fileids)
    await add_all_file(dbid, fileids)
    
    key = f"{message.chat.id}-{message.id}"
    KEYWORD[key] = search

    btn = [[
        InlineKeyboardButton(
            text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
            callback_data=f"uvew_{file.file_id}"
        ),
        InlineKeyboardButton(
            text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
            callback_data=f"uvew_{file.file_id}"
        )][:settings["button"]]
        for file in files
    ]
    #btn.insert(0,
    #           [
    #               InlineKeyboardButton(
    #                   f"๏ sᴇɴᴅ ᴀʟʟ ғɪʟᴇ ๏", url=await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=sendall_{dbid}", message.chat.id))
    #           ]
    #           )
    
    btn.insert(0, [
        InlineKeyboardButton("! Sᴇʟᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ !", callback_data=f"select_lang#{message.from_user.id}#{key}")
    ])    

    btn.insert(0, [
        InlineKeyboardButton("✅ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ✅",
                             url=settings["tutorial"] if "tutorial" in settings else 'https://t.me/Waiting_Area12')
    ])
    
    

    if offset != "":
        key = f"{message.chat.id}-{message.id}"
        BUTTONS[key] = search
        req = message.from_user.id if message.from_user else 0
        btn.append(
            [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
             InlineKeyboardButton(text="ɴᴇxᴛ ⏩", callback_data=f"next_{req}_{key}_{offset}")]
        )
    else:
        btn.append(
            [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
        )
    imdb = await get_poster(search, file=(files[0]).file_name) if settings["imdb"] else None
    TEMPLATE = settings['template']
    if imdb:
        cap = TEMPLATE.format(
            query=search,
            title=imdb['title'],
            votes=imdb['votes'],
            aka=imdb["aka"],
            seasons=imdb["seasons"],
            box_office=imdb['box_office'],
            localized_title=imdb['localized_title'],
            kind=imdb['kind'],
            imdb_id=imdb["imdb_id"],
            cast=imdb["cast"],
            runtime=imdb["runtime"],
            countries=imdb["countries"],
            certificates=imdb["certificates"],
            languages=imdb["languages"],
            director=imdb["director"],
            writer=imdb["writer"],
            producer=imdb["producer"],
            composer=imdb["composer"],
            cinematographer=imdb["cinematographer"],
            music_team=imdb["music_team"],
            distributors=imdb["distributors"],
            release_date=imdb['release_date'],
            year=imdb['year'],
            genres=imdb['genres'],
            poster=imdb['poster'],
            plot=imdb['plot'],
            rating=imdb['rating'],
            url=imdb['url'],
            **locals()
        )
    else:
        cap = f"<b><i>ᴍᴏᴠɪᴇ ɴᴀᴍᴇ : {search}\nʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\nɢʀᴏᴜᴘ : {message.chat.title}</i></b>"
    if imdb and imdb.get('poster'):
        try:
            hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await srh_msg.delete()
            await asyncio.sleep(300)
            await hehe.delete()
        except MediaEmpty | PhotoInvalidDimensions | WebpageMediaEmpty:
            pic = imdb.get('poster')
            poster = pic.replace('.jpg', "._V1_UX360.jpg")
            hmm = await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
            await srh_msg.delete()
            await asyncio.sleep(300)
            await hmm.delete()
        except Exception as e:
            logger.exception(e)
            reply_markup = InlineKeyboardMarkup(btn)
            await srh_msg.edit_text(text=cap, disable_web_page_preview=True)
            await srh_msg.edit_reply_markup(reply_markup)
            await asyncio.sleep(300)
            await srh_msg.delete()
    else:
        reply_markup = InlineKeyboardMarkup(btn)
        await srh_msg.edit_text(text=cap, disable_web_page_preview=True)
        await srh_msg.edit_reply_markup(reply_markup)
        await asyncio.sleep(300)
        await srh_msg.delete()


# ------------------------------------------------------------------------------------------------- #

async def advantage_spell_chok(client, message, srh_msg):
    query = re.sub(r"\b(pl(i|e)*?(s|z+|ease|se|ese|(e+)s(e)?)|((send|snd|giv(e)?|gib)(\sme)?)|movie(s)?|new|latest|br((o|u)h?)*|^h(e|a)?(l)*(o)*|mal(ayalam)?|t(h)?amil|file|that|find|und(o)*|kit(t(i|y)?)?o(w)?|thar(u)?(o)*w?|kittum(o)*|aya(k)*(um(o)*)?|full\smovie|any(one)|with\ssubtitle(s)?)","", message.text, flags=re.IGNORECASE)  # plis contribute some common words
    query_ = query #query.strip() + " movie"
    try:
        movies = await get_poster(remove_words2(message.text), bulk=True)
        logger.info(movies)

    except Exception as e:
        logger.exception(e)
        text = query_.replace(" ", "+")
        link = f"https://www.google.com/search?q={text}"
        button = [
            [
                InlineKeyboardButton(
                    text=f"Click Here To check Spelling ✅", url=link
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Click Here To check Release Date 📅", url=f"{link}%20realese%20date"
                )
            ]
        ]
        reply_markup = InlineKeyboardMarkup(button)
        await srh_msg.edit_text(
            text="<b>ᴏᴏᴘs ᴍᴏᴠɪᴇ ɴᴏᴛ ғᴏᴜɴᴅ 😳 ! \n\nᴘʟᴇᴀsᴇ sᴇᴀʀᴄʜ ʟɪᴋᴇ ᴛʜɪs 👇\n\nKgf 2 ✅\nKgf 2 hindi ✅\nKgf 2022 ✅</b>"
        )
        await srh_msg.edit_reply_markup(reply_markup)
        await asyncio.sleep(30)
        return await srh_msg.delete()

    movielist = []
    words = message.text.split()
    if len(words) > 1:
        longest_word = max(filter(lambda word: len(word) == max(map(len, words)), words), key=len)
        longest_word_ = re.sub(r'(?:{})'.format('|'.join(map(re.escape, WITHOUT_WORDS_IGNORE))), '', longest_word)
        longest_word_ = longest_word_.replace("  ", " ")
        logger.info(longest_word_)
    else:
        longest_word_ = message.text
    if not movies:
        files, offset, total_results = await get_search_results(longest_word_, offset=0, filter=True)
        if not files:
            text = query_.replace(" ", "+")
            link = f"https://www.google.com/search?q={text}"
            button = [
                [
                    InlineKeyboardButton(
                        text=f"Click Here To check Spelling ✅", url=link
                    )
                ],
                [
                    InlineKeyboardButton(
                        text=f"Click Here To check Release Date 📅", url=f"{link}%20realese%20date"
                    )
                ]
            ]
            reply_markup = InlineKeyboardMarkup(button)
            await srh_msg.edit_text(
                text="<b>ᴏᴏᴘs ᴍᴏᴠɪᴇ ɴᴏᴛ ғᴏᴜɴᴅ 😳 ! \n\nᴘʟᴇᴀsᴇ sᴇᴀʀᴄʜ ʟɪᴋᴇ ᴛʜɪs 👇\n\nKgf 2 ✅\nKgf 2 hindi ✅\nKgf 2022 ✅</b>"
            )
            await srh_msg.edit_reply_markup(reply_markup)
            await asyncio.sleep(30)
            await srh_msg.delete()
            return
    if movies:
        movielist += [f"{movie.get('title')} {movie.get('year')}" if movie.get(
            'year') else movie.get('title') for movie in movies]
        movie = movielist[0]
    elif files:
        movie = longest_word_
    settings = await db.get_settings(message.chat.id)

    k = await manual_filters(client, message, text=movie)
    if k == False:
        logger.info(movie)
        files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if not files and len(words) > 1:
            movie = longest_word_
            logger.info(movie)
            files, offset, total_results = await get_search_results(movie, offset=0, filter=True)
        if files:
            fileids = [file.file_id for file in files]
            dbid = fileids[0]
            fileids = "L_I_N_K".join(fileids)
            await add_all_file(dbid, fileids)
            key = f"{message.chat.id}-{message.id}"
            KEYWORD[key] = movie
            
            btn = [[
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
                    callback_data=f"uvew_{file.file_id}"
                ),
                InlineKeyboardButton(
                    text=f"[{get_size(file.file_size)}] {replace_username(file.file_name)}",
                    callback_data=f"uvew_{file.file_id}"
                )][:settings["button"]]
                for file in files
            ]
            #btn.insert(0,
            #           [
            #               InlineKeyboardButton(
            #                   f"๏ sᴇɴᴅ ᴀʟʟ ғɪʟᴇs ๏", url=await get_shortlink(f"https://telegram.me/{temp.U_NAME}?start=sendall_{dbid}", message.chat.id))
            #           ]
            #           )
            
            btn.insert(0, [
                InlineKeyboardButton("! Sᴇʟᴇᴄᴛ Lᴀɴɢᴜᴀɢᴇ !", callback_data=f"select_lang#{message.from_user.id}#{key}")
            ])    

            btn.insert(0, [
                InlineKeyboardButton("✅ ʜᴏᴡ ᴛᴏ ᴅᴏᴡɴʟᴏᴀᴅ ✅",
                                     url=settings["tutorial"] if "tutorial" in settings else 'https://t.me/Waiting_Area12') 
            ])

            if offset != "":
                key = f"{message.chat.id}-{message.id}"
                BUTTONS[key] = movie
                req = message.from_user.id if message.from_user else 0
                btn.append(
                    [InlineKeyboardButton(text=f"🗓 1/{math.ceil(int(total_results) / 10)}", callback_data="pages"),
                     InlineKeyboardButton(text="ɴᴇxᴛ ⏩", callback_data=f"next_{req}_{key}_{offset}")]
                )
            else:
                btn.append(
                    [InlineKeyboardButton(text="🗓 1/1", callback_data="pages")]
                )
            imdb = await get_poster(query, file=(files[0]).file_name) if settings["imdb"] else None
            TEMPLATE = settings['template']
            if imdb:
                cap = TEMPLATE.format(
                    query=query,
                    title=imdb['title'],
                    votes=imdb['votes'],
                    aka=imdb["aka"],
                    seasons=imdb["seasons"],
                    box_office=imdb['box_office'],
                    localized_title=imdb['localized_title'],
                    kind=imdb['kind'],
                    imdb_id=imdb["imdb_id"],
                    cast=imdb["cast"],
                    runtime=imdb["runtime"],
                    countries=imdb["countries"],
                    certificates=imdb["certificates"],
                    languages=imdb["languages"],
                    director=imdb["director"],
                    writer=imdb["writer"],
                    producer=imdb["producer"],
                    composer=imdb["composer"],
                    cinematographer=imdb["cinematographer"],
                    music_team=imdb["music_team"],
                    distributors=imdb["distributors"],
                    release_date=imdb['release_date'],
                    year=imdb['year'],
                    genres=imdb['genres'],
                    poster=imdb['poster'],
                    plot=imdb['plot'],
                    rating=imdb['rating'],
                    url=imdb['url'],
                    **locals()
                )
            else:
                cap = f"<b><i>ᴍᴏᴠɪᴇ ɴᴀᴍᴇ : {query}\nʀᴇǫᴜᴇsᴛᴇᴅ ʙʏ : {message.from_user.mention}\nɢʀᴏᴜᴘ : {message.chat.title}</i></b>"
            if imdb and imdb.get('poster'):
                try:
                    hehe = await message.reply_photo(photo=imdb.get('poster'), caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                    await srh_msg.delete()
                    await asyncio.sleep(300)
                    await hehe.delete()
                except MediaEmpty | PhotoInvalidDimensions | WebpageMediaEmpty:
                    pic = imdb.get('poster')
                    poster = pic.replace('.jpg', "._V1_UX360.jpg")
                    hmm = await message.reply_photo(photo=poster, caption=cap, reply_markup=InlineKeyboardMarkup(btn))
                    await srh_msg.delete()
                    await asyncio.sleep(300)
                    await hmm.delete()
                except Exception as e:
                    logger.exception(e)
                    reply_markup = InlineKeyboardMarkup(btn)
                    await srh_msg.edit_text(text=cap, disable_web_page_preview=True)
                    await srh_msg.edit_reply_markup(reply_markup)
                    await asyncio.sleep(300)
                    await srh_msg.delete()
            else:
                reply_markup = InlineKeyboardMarkup(btn)
                await srh_msg.edit_text(text=cap, disable_web_page_preview=True)
                await srh_msg.edit_reply_markup(reply_markup)
                await asyncio.sleep(300)
                await srh_msg.delete()

        else:
            movie = query_.replace(" ", "+")
            link = f"https://www.google.com/search?q={movie}"
            btn = [
            [
                InlineKeyboardButton(
                    text=f"Click Here To check Spelling ✅", url=link
                )
            ],
            [
                InlineKeyboardButton(
                    text=f"Click Here To check Release Date 📅", url=f"{link}%20realese%20date"
                )
            ]
        ]
            reply_markup = InlineKeyboardMarkup(btn)
            k = await srh_msg.edit_text('<b>ᴏᴏᴘs ᴍᴏᴠɪᴇ ɴᴏᴛ ғᴏᴜɴᴅ 😳 ! \n\nᴘʟᴇᴀsᴇ sᴇᴀʀᴄʜ ʟɪᴋᴇ ᴛʜɪs 👇\n\nKgf 2 ✅\nKgf 2 hindi ✅\nKgf 2022 ✅</b>')
            await k.edit_reply_markup(reply_markup)
            await asyncio.sleep(30)
            await k.delete()


# ------------------------------------------------------------------------------------------------- #

async def manual_filters(client, message, text=False):
    group_id = message.chat.id
    name = text or message.text
    reply_id = message.reply_to_message.id if message.reply_to_message else message.id
    keywords = await get_filters(group_id)
    for keyword in reversed(sorted(keywords, key=len)):
        pattern = r"( |^|[^\w])" + re.escape(keyword) + r"( |$|[^\w])"
        if re.search(pattern, name, flags=re.IGNORECASE):
            reply_text, btn, alert, fileid = await find_filter(group_id, keyword)

            if reply_text:
                reply_text = reply_text.replace(
                    "\\n", "\n").replace("\\t", "\t")

            if btn is not None:
                try:
                    if fileid == "None":
                        if btn == "[]":
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_to_message_id=reply_id)
                        else:
                            button = eval(btn)
                            await client.send_message(
                                group_id,
                                reply_text,
                                disable_web_page_preview=True,
                                reply_markup=InlineKeyboardMarkup(button),
                                reply_to_message_id=reply_id
                            )
                    elif btn == "[]":
                        await client.send_cached_media(
                            group_id,
                            fileid,
                            caption=reply_text or "",
                            reply_to_message_id=reply_id
                        )
                    else:
                        button = eval(btn)
                        await message.reply_cached_media(
                            fileid,
                            caption=reply_text or "",
                            reply_markup=InlineKeyboardMarkup(button),
                            reply_to_message_id=reply_id
                        )
                except Exception as e:
                    logger.exception(e)
                break
    else:
        return False
  

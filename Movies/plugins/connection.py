from pyrogram import filters, Client, enums
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from Movies.database.connections import add_connection, all_connections, if_active, delete_connection
from config import ADMINS, LOG_CHANNEL
from script import script
from Movies.database.chats import db
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.ERROR)


# --------------------» ᴄᴏɴɴᴇᴄᴛ «---------------------- #

@Client.on_message((filters.private | filters.group) & filters.command('connect'))
async def addconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        try:
            cmd, group_id = message.text.split(" ", 1)
        except:
            await message.reply_text(
                "<b>ᴇɴᴛᴇʀ ɪɴ ᴄᴏʀʀᴇᴄᴛ ғᴏʀᴍᴀᴛ !</b>\n\n"
                "<code>/connect ɢʀᴏᴜᴘ ɪᴅ</code>\n\n"
                "<i>ɢᴇᴛ ʏᴏᴜʀ ɢʀᴏᴜᴘ ɪᴅ ʙʏ ᴀᴅᴅɪɴɢ ᴛʜɪs ʙᴏᴛ ᴛᴏ ʏᴏᴜʀ ɢʀᴏᴜᴘ ᴀɴᴅ ᴜsᴇ <code>/id</code></i>",
                quote=True
            )
            return

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

    try:
        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and userid not in ADMINS
        ):
            await message.reply_text("ʏᴏᴜ sʜᴏᴜʟᴅ ʙᴇ ᴀɴ ᴀᴅᴍɪɴ ɪɴ ɢɪᴠᴇɴ ɢʀᴏᴜᴘ!", quote=True)
            return
    except Exception as e:
        logger.exception(e)
        await message.reply_text(
            "ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ !\n\nɪғ ᴄᴏʀʀᴇᴄᴛ, ᴍᴀᴋᴇ sᴜʀᴇ ɪ'ᴍ ᴘʀᴇsᴇɴᴛ ɪɴ ʏᴏᴜʀ ɢʀᴏᴜᴘ !!",
            quote=True,
        )

        return
    try:
        st = await client.get_chat_member(group_id, "me")
        if st.status == enums.ChatMemberStatus.ADMINISTRATOR:
            ttl = await client.get_chat(group_id)
            title = ttl.title

            addcon = await add_connection(str(group_id), str(userid))
            if addcon:
                if not await db.get_chat(group_id):
                    total=await client.get_chat_members_count(group_id)
                    await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(title, group_id, total, "Unknown"))       
                    await db.add_chat(group_id, title) 
                await message.reply_text(
                    f"sᴜᴄᴄᴇssғᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛ ᴛᴏ**{title}**\nɴᴏᴡ ʏᴏᴜ ᴄᴀɴ ᴍᴀɴᴀɢᴇ ʏᴏᴜʀ ɢʀᴏᴜᴘ ғʀᴏᴍ ʜᴇʀᴇ../",
                    quote=True,
                    parse_mode=enums.ParseMode.MARKDOWN
                )
                if chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
                    await client.send_message(
                        userid,
                        f"ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ **{title}** !",
                        parse_mode=enums.ParseMode.MARKDOWN
                    )
            else:
                await message.reply_text(
                    "ʏᴏᴜ'ʀᴇ ᴀʟʀᴇᴀᴅʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴛʜɪs ᴄʜᴀᴛ !",
                    quote=True
                )
        else:
            await message.reply_text("ᴀᴅᴅ ᴍᴇ ᴀs ᴀɴ ᴀᴅᴍɪɴ ɪɴ ɢʀᴏᴜᴘ.", quote=True)
    except Exception as e:
        logger.exception(e)
        await message.reply_text('sᴏᴍᴇ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ ! ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.', quote=True)
        return


# --------------------» ᴅɪs-ᴄᴏɴɴᴇᴄᴛ «---------------------- #

@Client.on_message((filters.private | filters.group) & filters.command('disconnect'))
async def deleteconnection(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"ʏᴏᴜ ᴀʀᴇ ᴀɴᴏɴʏᴍᴏᴜs ᴀᴅᴍɪɴ. ᴜsᴇ /connect {message.chat.id} ɪɴ ᴘᴍ")
    chat_type = message.chat.type

    if chat_type == enums.ChatType.PRIVATE:
        await message.reply_text("ʀᴜɴ /connections ᴛᴏ ᴠɪᴇᴡ ᴏʀ ᴅɪsᴄᴏɴɴᴇᴄᴛ ғʀᴏᴍ ɢʀᴏᴜᴘs !", quote=True)

    elif chat_type in [enums.ChatType.GROUP, enums.ChatType.SUPERGROUP]:
        group_id = message.chat.id

        st = await client.get_chat_member(group_id, userid)
        if (
                st.status != enums.ChatMemberStatus.ADMINISTRATOR
                and st.status != enums.ChatMemberStatus.OWNER
                and str(userid) not in ADMINS
        ):
            return

        delcon = await delete_connection(str(userid), str(group_id))
        if delcon:
            await message.reply_text("sᴜᴄᴄᴇssғᴜʟʟʏ ᴅɪsᴄᴏɴɴᴇᴄᴛᴇᴅ ғʀᴏᴍ ᴛʜɪs ᴄʜᴀᴛ", quote=True)
        else:
            await message.reply_text("ᴛʜɪs ᴄʜᴀᴛ ɪsɴ'ᴛ ᴄᴏɴɴᴇᴄᴛᴇᴅ ᴛᴏ ᴍᴇ !\nᴅᴏ /connect ᴛᴏ ᴄᴏɴɴᴇᴄᴛ.", quote=True)


# --------------------» ᴄᴏɴɴᴇᴄᴛɪᴏɴ «---------------------- #

@Client.on_message(filters.private & filters.command(["connections"]))
async def connections(client, message):
    userid = message.from_user.id

    groupids = await all_connections(str(userid))
    if groupids is None:
        await message.reply_text(
            "ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs !! ᴄᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ.",
            quote=True
        )
        return
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
        await message.reply_text(
            "ᴄᴏɴɴᴇᴄᴛᴇᴅ ɢʀᴏᴜᴘs :-\n\n",
            reply_markup=InlineKeyboardMarkup(buttons),
            quote=True
        )
    else:
        await message.reply_text(
            "ᴛʜᴇʀᴇ ᴀʀᴇ ɴᴏ ᴀᴄᴛɪᴠᴇ ᴄᴏɴɴᴇᴄᴛɪᴏɴs !! ᴄᴏɴɴᴇᴄᴛ ᴛᴏ sᴏᴍᴇ ɢʀᴏᴜᴘs ғɪʀsᴛ.",
            quote=True
                  )
                  

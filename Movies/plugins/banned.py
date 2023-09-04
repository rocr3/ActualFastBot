from pyrogram import Client, filters
from Movies.utils import temp
from pyrogram.types import Message
from Movies.database.chats import db
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import SUPPORT_CHAT

# ------------------» ʙᴀɴ-ᴜsᴇʀ-ᴄʟɪᴇɴᴛ «------------------ # 

async def banned_users(_, client, message: Message):
    return (
        message.from_user is not None or not message.sender_chat
    ) and message.from_user.id in temp.BANNED_USERS

banned_user = filters.create(banned_users)

async def disabled_chat(_, client, message: Message):
    return message.chat.id in temp.BANNED_CHATS

disabled_group=filters.create(disabled_chat)



# ------------------» ʙᴀɴ-ᴜsᴇʀ «------------------ # 

@Client.on_message(filters.private & banned_user & filters.incoming)
async def ban_reply(bot, message):
    ban = await db.get_ban_status(message.from_user.id)
    await message.reply(f'<b>sᴘʀʀʏ ᴅᴜᴅᴇ, ʏᴏᴜ ᴀʀᴇ ʙᴀɴɴᴇᴅ ᴛᴏ ᴜsᴇ ᴍᴇ.</b>\n\nʙᴀɴ ʀᴇᴀsᴏɴ: {ban["ban_reason"]}')

@Client.on_message(filters.group & disabled_group & filters.incoming)
async def grp_bd(bot, message):
    buttons = [[
        InlineKeyboardButton('sᴜᴘᴘᴏʀᴛ', url=f'https://t.me/{SUPPORT_CHAT}')
    ]]
    reply_markup=InlineKeyboardMarkup(buttons)
    vazha = await db.get_chat(message.chat.id)
    k = await message.reply(
        text=f"<b>ᴄʜᴀᴛ ɴᴏᴛ ᴀʟʟᴏᴡᴇᴅ 🐞</b>\n\n<b>ᴍʏ ᴀᴅᴍɪɴs ʜᴀs ʀᴇsᴛʀɪᴄᴛᴇᴅ ᴍᴇ ғʀᴏᴍ ᴡᴏʀᴋɪɴɢ ʜᴇʀᴇ ! ɪғ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴋɴᴏᴡ ᴍᴏʀᴇ ᴀʙᴏᴜᴛ ɪᴛ ᴄᴏɴᴛʀᴀᴄᴛ sᴜᴘᴘᴏʀᴛ.</b>\nʀᴇᴀsᴏɴ : <code>{vazha['reason']}</code>.",
        reply_markup=reply_markup)
    try:
        await k.pin()
    except:
        pass
    await bot.leave_chat(message.chat.id)
      

from telethon import TelegramClient
from telethon.tl.types import InputPeerUser
from telethon.tl.custom import Message


from settings import BOT_USERNAME


async def send_message_via_telethon(telethon: TelegramClient, message: str) -> None:
    bot_username = BOT_USERNAME
    bot_entity = await telethon.get_entity(bot_username)
    bot_peer = InputPeerUser(user_id=bot_entity.id, access_hash=bot_entity.access_hash)
    await telethon.send_message(entity=bot_peer, message=message)


async def check_message_history(telethon: TelegramClient, username):
    messages = await telethon.get_messages(username, limit=1)
    print(messages)
    return is_account_limited(messages[0])


def is_account_limited(msg: Message) -> bool:
    kb = msg.reply_markup
    if kb and hasattr(kb, "rows") and len(kb.rows) >= 4:
        return True

    text = (msg.message or "").lower()
    if "no limits are currently applied" in text or "свободен" in text:
        return False
    
    if "account was limited" in text or "account is limited" in text:
        return True

    if kb and hasattr(kb, "rows") and len(kb.rows) == 2:
        return False
    return False
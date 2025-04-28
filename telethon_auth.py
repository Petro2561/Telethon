import asyncio
import json
from dataclasses import dataclass
from pathlib import Path
import re

import telethon

from proxies import get_random_socks5_proxy
from telethon import TelegramClient
from typing import List

from settings import BOT_USERNAME
from spam_check import check_message_history, send_message_via_telethon

FOLDER_NAME = "accounts"


@dataclass
class Account:
    session: Path
    app_id: int
    app_hash: str
    device: str
    sdk: str
    app_version: str
    lang_code: str
    system_lang_code: str
    use_ipv6: bool
    phone: str
    password: str


class Auth:
    def __init__(self, folder: str = FOLDER_NAME):
        self.folder = Path(folder)

    async def get_all_accounts(self) -> list[Account]:
        accounts: list[Account] = []
        for json_f in self.folder.glob("*.json"):
            sess_f = self.folder / (json_f.stem + ".session")
            if not sess_f.exists():
                continue
            cfg = json.loads(json_f.read_text())
            accounts.append(Account(
                session=sess_f,
                app_id=cfg["app_id"],
                app_hash=cfg["app_hash"],
                device=cfg.get("device_model", "PC"),
                sdk=cfg.get("system_version", "Unknown"),
                app_version=cfg.get("app_version", "1.0"),
                lang_code=cfg.get("lang_code", "en"),
                system_lang_code=cfg.get("system_lang_code", "en"),
                use_ipv6=cfg.get("use_ipv6", False),
                phone=cfg.get("phone"),
                password=cfg.get("twoFA")
            ))
        return accounts


    async def initialize_account(self, account: Account, proxy, session) -> TelegramClient:
        return TelegramClient(
            session=session,
            api_id=account.app_id,
            api_hash=account.app_hash,
            device_model=account.device,
            system_version=account.sdk,
            app_version=account.app_version,
            lang_code=account.lang_code,
            system_lang_code=account.system_lang_code,
            use_ipv6=account.use_ipv6,
            proxy=proxy,
        )

    async def auth(self):
        accounts = await self.get_all_accounts()
        stats = {
            "unauthorized": [],
            "limited": [],
            "unlimited": []
        }
        for account in accounts:
            print(f"\n→ {account.session.name}")
            name = account.session.name
            for attempt in range(1, 6):
                proxy = await get_random_socks5_proxy()
                print(f"  Попытка {attempt}: via {proxy[1]}:{proxy[2]}")
                client = await self.initialize_account(account, proxy, session=account.session)
                try:
                    await client.connect()
                except Exception as e:
                    print("    ⚠ Ошибка подключения:", e)
                    await client.disconnect()
                    continue

                if not await client.is_user_authorized():
                    print("    ❌ Не авторизован, требуется код или пароль")
                    stats["unauthorized"].append(name)
                    await client.disconnect()
                    break
                try:
                    me_entity = await client.get_entity("me")
                    print("    ✅ (из get_entity) пользователь:", me_entity.username or me_entity.first_name)
                    new_client = await self.initialize_account(account, proxy, session=f"new_{account.session.name}.session")
                    await new_client.connect()
                    sent = await new_client.send_code_request(account.phone, force_sms=False)
                    await asyncio.sleep(1)
                    messages = await client.get_messages(777000, limit=1)
                    text = messages[0].message
                    m = re.search(r"\b(\d{5,6})\b", text)
                    if not m:
                        raise RuntimeError(f"Не найден код в сообщении: {text!r}")
                    code = m.group(1)
                    print("Пойман код:", code)
                    try:
                        await new_client.sign_in(phone=account.phone, code=code, phone_code_hash=sent.phone_code_hash)
                    except telethon.errors.SessionPasswordNeededError:
                        await new_client.sign_in(password=account.password)
                    await asyncio.sleep(1)
                    await send_message_via_telethon(telethon=new_client, message="/start")
                    await asyncio.sleep(3)
                    is_limited = await check_message_history(telethon=new_client, username=BOT_USERNAME)
                    if is_limited:
                        print("    🚫 Аккаунт ограничен спам-ботом")
                        stats["limited"].append(name)
                    else:
                        print("    ✅ Аккаунт без ограничений")
                        stats["unlimited"].append(name)
                except AttributeError:
                    print("    ✅ Успешно, но не удалось получить данные профиля")
                    stats["unlimited"].append(name)
                finally:
                    await client.disconnect()
                    await new_client.disconnect()
                break

            else:
                print(f"  ❌ Все 5 попыток неудачны для {account.session.name}")
                stats["unauthorized"].append(name)
        return stats

import random
import aiohttp
import socks


API_KEY = "4a29fcbd2d3c2e457e54c0ae369db1f7"
API_URL = f"http://api.best-proxies.ru/proxylist.json?key={API_KEY}&limit=0&type=socks5"


async def fetch_proxies_for_telethon():
    async with aiohttp.ClientSession() as session:
        async with session.get(API_URL, timeout=10) as resp:
            resp.raise_for_status()
            raw = await resp.json()
            return raw


async def get_random_socks5_proxy():
    raw = await fetch_proxies_for_telethon()
    if not raw:
        raise RuntimeError("Список прокси пуст")
    item = random.choice(raw)
    host = item["ip"]
    port = int(item["port"])
    return (socks.SOCKS5, host, port)

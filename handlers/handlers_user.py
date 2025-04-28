from io import BytesIO
import io
from pathlib import Path
import uuid
from aiogram import F, Bot, Router
from aiogram.filters import Command, StateFilter, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from aiogram.enums import ContentType
import rarfile

from handlers.utils import extract_rar_to_dir
from settings import PROXIES
from telethon_auth import Auth



START_MESSAGE = """<b>Привет, {name}!</b>

Отправьте архив zip или rar с аккаунтами и я скажу количество аккаунтов со спам-блоком и количество без.
"""


router = Router()


@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext, command: CommandObject, bot: Bot):
    await message.answer(START_MESSAGE.format(name=message.from_user.first_name), parse_mode="HTML")


@router.message()
async def start_command(message: Message, state: FSMContext, bot: Bot):
    if message.document:
        await message.answer("Файл принят, нужно немного подождать")
        file = await bot.get_file(message.document.file_id)
        file_path = file.file_path
        data: io.BytesIO = await bot.download_file(file_path)
        session_id = uuid.uuid4().hex
        accounts_dir = Path("accounts") / session_id
        extracted = await extract_rar_to_dir(data, accounts_dir)
        await message.answer(f"Извлечено аккаунтов: {extracted}")
        stats = await Auth(folder=accounts_dir).auth()
        text = (
            f"📊 Статистика проверки аккаунтов:\n\n"
            + f"👤 Не удалось авторизоваться: {len(stats['unauthorized'])}"
            + "".join(f"\n  {name}" for name in stats['unauthorized'])
            + "\n\n"
            + f"🚫 Ограничены спам-ботом: {len(stats['limited'])}"
            + "".join(f"\n  {name}" for name in stats['limited'])
            + "\n\n"
            + f"✅ Без ограничений: {len(stats['unlimited'])}"
            + "".join(f"\n  {name}" for name in stats['unlimited'])
        )
        await message.answer(text)

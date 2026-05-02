import logging
from aiogram import Bot
from aiogram.client.bot import Bot as AiogramBot

logger = logging.getLogger(__name__)

class TelegramClient:
    """
    Ares Quant bildirim sistemini yöneten istemci.
    """
    def __init__(self, token: str):
        self.bot = Bot(token=token)
        logger.info("📱 Telegram Bildirim Sistemi Hazır.")

    async def send(self, chat_id: str, message: str):
        """
        Belirtilen kanala veya kullanıcıya mesaj gönderir.
        """
        try:
            # aiogram 3.x versiyonu için send_message kullanımı
            await self.bot.send_message(chat_id=chat_id, text=message, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"❌ Telegram Mesaj Gönderim Hatası: {e}")

    async def send_photo(self, chat_id: str, photo_path: str, caption: str):
        """
        Siyah tema grafiklerini kanala gönderir.
        """
        try:
            from aiogram.types import FSInputFile
            photo = FSInputFile(photo_path)
            await self.bot.send_photo(chat_id=chat_id, photo=photo, caption=caption, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"❌ Telegram Fotoğraf Gönderim Hatası: {e}")

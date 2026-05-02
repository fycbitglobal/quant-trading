import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    # =========================
    # BOT AYARLARI
    # =========================
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    OUTPUT_CHANNEL = os.getenv("OUTPUT_CHANNEL")

    # =========================
    # 🔥 TRADING MODE
    # =========================
    PAPER_MODE = os.getenv("PAPER_MODE", "true").lower() == "true"

    # =========================
    # EXCHANGES
    # =========================
    EXCHANGES = {
        "BINANCE": {
            "api_key": os.getenv("BINANCE_API_KEY"),
            "secret_key": os.getenv("BINANCE_SECRET_KEY"),
            "enabled": True
        },
        "FYCBIT": {
            "api_key": os.getenv("FYCBIT_API_KEY"),
            "secret_key": os.getenv("FYCBIT_SECRET_KEY"),
            "enabled": False
        },
        "OKX": {
            "api_key": os.getenv("OKX_API_KEY"),
            "secret_key": os.getenv("OKX_SECRET_KEY"),
            "enabled": False
        },
        "BYBIT": {
            "api_key": os.getenv("BYBIT_API_KEY"),
            "secret_key": os.getenv("BYBIT_SECRET_KEY"),
            "enabled": False
        }
    }


config = Config()
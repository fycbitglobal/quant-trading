import logging
from typing import Dict, Any, List, Optional
from .base import BaseExchange
from binance import AsyncClient

logger = logging.getLogger(__name__)

class BinanceClient(BaseExchange):
    def __init__(self, api_key: str, secret_key: str):
        super().__init__(api_key, secret_key)
        self._client = None

    async def _get_client(self) -> AsyncClient:
        """Tek bir AsyncClient oturumu oluşturur ve bunu tekrar kullanır."""
        if self._client is None:
            try:
                self._client = AsyncClient(self.api_key, self.secret_key)
                logger.info("✅ Binance AsyncClient oturumu başarıyla oluşturuldu.")
            except Exception as e:
                logger.error(f"Binance Bağlantı Hatası: {e}")
        return self._client

    async def get_ticker(self, symbol: str) -> float:
        try:
            client = await self._get_client()
            res = await client.get_symbol_ticker(symbol=symbol)
            return float(res['price'])
        except Exception as e:
            # Sembol hataları için log seviyesini düşürdük (Ekran kirliliği önlemek için)
            if "Invalid symbol" in str(e):
                logger.warning(f"Sema Hatası: {symbol} geçersiz bir sembol.")
            else:
                logger.error(f"Binance Ticker Hatası ({symbol}): {e}")
            return 0.0

    async def get_historical_klines(self, symbol: str, interval: str, limit: int) -> List[List]:
        try:
            client = await self._get_client() # CLEANED
            client = await self._get_client()
            return await client.get_klines(symbol=symbol, interval=interval, limit=limit)
        except Exception as e:
            if "Invalid symbol" in str(e):
                logger.warning(f"Sema Hatası: {symbol} geçersiz bir sembol.")
            else:
                logger.error(f"Binance K-lines Hatası ({symbol}): {e}")
            return []

    async def place_order(self, symbol: str, side: str, amount: float, price: float = None) -> Dict[str, Any]:
        try:
            client = await self._get_client()
            order_type = "LIMIT" if price else "MARKET"
            return await client.create_order(symbol=symbol, side=side, type=order_type, quantity=amount, price=price)
        except Exception as e:
            logger.error(f"Binance Order Hatası: {e}")
            return {"error": str(e)}

    async def get_balance(self, asset: str) -> float:
        try:
            client = await self._get_client()
            res = await client.get_asset_balance(asset=asset)
            return float(res['free'])
        except Exception as e:
            logger.error(f"Binance Bakiye Hatası: {e}")
            return 0.0

    async def close_session(self):
        """Program kapanırken oturumu düzgünce kapatır."""
        if self._client:
            await self._client.close_connection()
            logger.info("🔌 Binance oturumu güvenli bir şekilde kapatıldı.")

    async def stream_market_data(self, symbol: str):
        pass

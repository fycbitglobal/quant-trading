from typing import Dict, Any, List, Optional # <--- Bu satır eksikti
from .binance import BinanceClient
from .fycbit import FycbitClient
from app.core.config import config
class ExchangeManager:
    def __init__(self):
        self.clients = {}
        self._initialize_clients()

    def _initialize_clients(self):
        """Config dosyasındaki aktif borsaları başlatır."""
        if config.EXCHANGES["BINANCE"]["enabled"]:
            self.clients["BINANCE"] = BinanceClient(
                config.EXCHANGES["BINANCE"]["api_key"], 
                config.EXCHANGES["BINANCE"]["secret_key"]
            )
            
        if config.EXCHANGES["FYCBIT"]["enabled"]:
            self.clients["FYCBIT"] = FycbitClient(
                config.EXCHANGES["FYCBIT"]["api_key"], 
                config.EXCHANGES["FYCBIT"]["secret_key"]
            )

    async def get_best_price(self, symbol: str) -> Dict[str, Any]:
        """Tüm aktif borsaları tarayıp en iyi fiyatı döndürür."""
        prices = {}
        for name, client in self.clients.items():
            price = await client.get_ticker(symbol)
            if price > 0:
                prices[name] = price
        
        if not prices:
            return {"exchange": None, "price": 0.0}
        
        # En düşük fiyatlı borsayı seç (Sadece Alım için)
        best_exchange = min(prices, key=prices.get)
        return {"exchange": best_exchange, "price": prices[best_exchange]}

    def get_client(self, exchange_name: str):
        """Belirli bir borsanın istemcisini döndürür."""
        return self.clients.get(exchange_name.upper())

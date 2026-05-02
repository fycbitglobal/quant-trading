from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseExchange(ABC):
    """
    Tüm borsa adaptörlerinin uyması gereken temel sınıftır.
    Bu sınıf sayesinde 'Main Engine' borsanın ismini bilmeden 
    işlem yapabilir.
    """
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    @abstractmethod
    async def get_ticker(self, symbol: str) -> float:
        """Anlık fiyatı döner."""
        pass

    @abstractmethod
    async def place_order(self, symbol: str, side: str, amount: float, price: float = None) -> Dict[str, Any]:
        """Alım veya Satım emri gönderir."""
        pass

    @abstractmethod
    async def get_balance(self, asset: str) -> float:
        """Belirli bir varlığın bakiyesini döner."""
        pass

    @abstractmethod
    async def stream_market_data(self, symbol: str):
        """WebSocket üzerinden anlık veri akışı sağlar."""
        pass

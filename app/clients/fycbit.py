import logging
import hmac
import hashlib
import time
import aiohttp
from typing import Dict, Any, Optional
from .base import BaseExchange

logger = logging.getLogger(__name__)

class FycbitClient(BaseExchange):
    def __init__(self, api_key: str, secret_key: str):
        super().__init__(api_key, secret_key)
        # ⚠️ ÖNEMLİ: Eğer borsa URL'sini değiştirdiyse burayı güncelle.
        # Genellikle /api/v1 veya /v1 şeklinde olur.
        self.base_url = "https://api.fycbit.com" 
        self.timeout = aiohttp.ClientTimeout(total=10)

    def _generate_signature(self, params: Dict[str, Any]) -> str:
        """
        Borsa standartlarına uygun HMAC-SHA256 imzası oluşturur.
        """
        # Parametreleri alfabetik sıraya diz ve query string oluştur
        query_string = "&".join([f"{k}={v}" for k, v in sorted(params.items())])
        return hmac.new(
            self.secret_key.encode('utf-8'), 
            query_string.encode('utf-8'), 
            hashlib.sha256
        ).hexdigest()

    async def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """
        Tüm API isteklerini yöneten merkez mekanizma.
        Hata kontrolü, imzalama ve timeout işlemlerini burada yapar.
        """
        url = f"{self.base_url}{endpoint}"
        
        # Zaman damgası ekle (Hầu hết borsalar bunu zorunlu kılar)
        if params is None: params = {}
        params['timestamp'] = int(time.time() * 1000)
        
        # Güvenlik imzasını ekle
        params['signature'] = self._generate_signature(params)
        
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json"
        }

        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                if method == "GET":
                    async with session.get(url, params=params, headers=headers) as resp:
                        return await self._handle_response(resp)
                elif method == "POST":
                    async with session.post(url, json=params, headers=headers) as resp:
                        return await self._handle_response(resp)
        except Exception as e:
            logger.error(f"FYCBIT Network Hatası: {e}")
            return None

    async def _handle_response(self, resp) -> Optional[Dict]:
        """Yanıtı analiz eder ve hata varsa loglar."""
        if resp.status == 200:
            try:
                return await resp.json()
            except Exception:
                logger.error(f"FYCBIT JSON Decode Hatası: {resp.status}")
                return None
        else:
            text = await resp.text()
            logger.error(f"FYCBIT API Hatası: Status {resp.status} | Response: {text}")
            return None

    async def get_ticker(self, symbol: str) -> float:
        """
        Fiyat bilgisini çeker. 
        URL '/v1/ticker' değilse, burayı borsanın dökümanına göre güncellemelisin.
        """
        endpoint = "/v1/ticker" # ⚠️ Burayı borsanın güncel endpoint'i ile değiştir
        params = {"symbol": symbol}
        
        res = await self._request("GET", endpoint, params)
        if res and 'price' in res:
            return float(res['price'])
        elif res and 'data' in res and 'price' in res['data']:
            return float(res['data']['price'])
        
        return 0.0

    async def place_order(self, symbol: str, side: str, amount: float, price: float = None) -> Dict[str, Any]:
        endpoint = "/v1/order"
        params = {
            "symbol": symbol,
            "side": side,
            "amount": amount,
            "type": "LIMIT" if price else "MARKET"
        }
        if price: params["price"] = price
        
        res = await self._request("POST", endpoint, params)
        return res if res else {"error": "Sipariş gönderilemedi."}

    async def get_balance(self, asset: str) -> float:
        endpoint = "/v1/balance"
        params = {"asset": asset}
        
        res = await self._request("GET", endpoint, params)
        if res and 'free' in res:
            return float(res['free'])
        return 0.0

    async def stream_market_data(self, symbol: str):
        pass

import logging
from typing import Dict, Any, Optional, List # <--- Eksikse ekle

logger = logging.getLogger(__name__)

class OrderflowAnalyzer:
    def __init__(self):
        self.cum_volume = 0.0
        self.cum_pv = 0.0
        self.vwap = 0.0

    def update_vwap(self, price: float, volume: float):
        """Kurumsal referans noktası olan VWAP'ı hesaplar."""
        self.cum_pv += (price * volume)
        self.cum_volume += volume
        self.vwap = self.cum_pv / self.cum_volume if self.cum_volume > 0 else price
        return self.vwap

    def calculate_imbalance(self, bids: List[List], asks: List[List], depth: int = 50) -> float:
        """
        Orderbook Imbalance: Alış ve Satış duvarları arasındaki fark.
        Pozitif = Boğa baskısı, Negatif = Ayı baskısı.
        """
        bid_vol = sum([float(bid[1]) for bid in bids[:depth]])
        ask_vol = sum([float(ask[1]) for ask in asks[:depth]])
        
        if (bid_vol + ask_vol) == 0: return 0.0
        return (bid_vol - ask_vol) / (bid_vol + ask_vol)

    def detect_liquidity_sweep(self, current_price: float, prev_high: float, prev_low: float, high: float, low: float):
        """SMC: Likidite temizleme (Stop Hunt) tespiti."""
        if high > prev_high and current_price < prev_high:
            return "BEARISH_SWEEP" # Tepedeki likidite temizlendi, fiyat aşağı dönebilir.
        if low < prev_low and current_price > prev_low:
            return "BULLISH_SWEEP" # Dipteki likidite temizlendi, fiyat yukarı dönebilir.
        return None

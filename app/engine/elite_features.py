# app/engine/elite_features.py (Yeni Modül)

class EliteAnalyzer:
    def __init__(self):
        self.orderbook_imbalance = 0.0
        self.vwap_value = 0.0
        self.cum_volume = 0.0
        self.cum_pv = 0.0

    def update_vwap(self, price: float, volume: float):
        """Kümülatif VWAP hesaplar."""
        self.cum_pv += (price * volume)
        self.cum_volume += volume
        self.vwap_value = self.cum_pv / self.cum_volume if self.cum_volume > 0 else price

    def calculate_imbalance(self, bids: List[List], asks: List[List], depth: int = 20):
        """
        Orderbook imbalance hesaplar. 
        Büyük alış duvarları varsa pozitif, satış varsa negatif döner.
        """
        total_bid_vol = sum([float(bid[1]) for bid in bids[:depth]])
        total_ask_vol = sum([float(ask[1]) for ask in asks[:depth]])
        
        if total_ask_vol == 0: return 1.0 # Maksimum bullish
        
        # (Bid - Ask) / (Bid + Ask) -> -1 ile 1 arası değer üretir
        self.orderbook_imbalance = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)
        return self.orderbook_imbalance

    def detect_liquidity_sweep(self, high: float, low: float, prev_high: float, prev_low: float, current_price: float):
        """
        Liquidity Sweep tespiti:
        Fiyat eski tepenin üzerine çıkar ama hemen altında kapatırsa -> Bearish Sweep
        """
        if high > prev_high and current_price < prev_high:
            return "BEARISH_SWEEP"
        if low < prev_low and current_price > prev_low:
            return "BULLISH_SWEEP"
        return None

from dataclasses import dataclass

@dataclass
class MarketStructure:
    trend: str # BULLISH, BEARISH, RANGING
    last_bos: bool = False # Break of Structure
    last_choch: bool = False # Change of Character

class SMCAnalyzer:
    def __init__(self):
        self.prev_high = 0.0
        self.prev_low = 0.0

    def analyze_structure(self, df) -> MarketStructure:
        """
        SMC Analizi: Fiyatın tepe ve dip yaptığı noktaları takip ederek 
        yapı kırılımlarını tespit eder.
        """
        last_close = df['close'].iloc[-1]
        high = df['high'].iloc[-1]
        low = df['low'].iloc[-1]
        
        bos = False
        choch = False
        trend = "RANGING"

        if self.prev_high > 0:
            if high > self.prev_high: # Market yapı kırılımı (BoS)
                bos = True
                trend = "BULLISH"
            elif low < self.prev_low:
                bos = True
                trend = "BEARISH"

        self.prev_high = high
        self.prev_low = low
        
        return MarketStructure(trend=trend, last_bos=bos, last_choch=choch)

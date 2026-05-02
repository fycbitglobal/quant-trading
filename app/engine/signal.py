import logging
import pandas as pd
import pandas_ta as ta
import numpy as np
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)

@dataclass
class Signal:
    symbol: str
    direction: str
    score: float
    confidence: str
    factors: List[str]
    entry_zone: tuple
    stop_loss: float
    take_profit: float
    exit_target: Optional[float] = None

class QuantAnalysisEngine:
    def __init__(self, binance_client):
        self.client = binance_client
        self.WEIGHTS = {
            "SMC_STRUCTURE": 0.35,
            "INSTITUTIONAL": 0.30,
            "TREND_SENSE": 0.20,
            "MOMENTUM_SENSE": 0.15
        }

    async def _fetch_comprehensive_data(self, symbol: str):
        try:
            res_1d = await self.client.get_historical_klines(symbol, '1d', 100)
            res_4h = await self.client.get_historical_klines(symbol, '4h', 200)
            res_15m = await self.client.get_historical_klines(symbol, '15m', 100)

            if not res_1d or not res_4h or not res_15m:
                return None, None, None

            cols = ['time','open','high','low','close','volume',
                    'close_time','quote_av','trades','buy_base','buy_quote','ignore']

            dfs = []
            for res in [res_1d, res_4h, res_15m]:
                df = pd.DataFrame(res)
                df.columns = cols
                df[['open','high','low','close','volume']] = df[['open','high','low','close','volume']].astype(float)
                dfs.append(df)

            return dfs[0], dfs[1], dfs[2]
        except Exception as e:
            logger.error(f"Data fetch error ({symbol}): {e}")
            return None, None, None

    def _analyze_smc(self, df):
        if df is None or len(df) < 25: return 0, ["SMC: Insufficient Data"]
        score, reasons = 0, []
        last_close = df['close'].iloc[-1]
        recent_high = df['high'].iloc[-20:-1].max()
        recent_low = df['low'].iloc[-20:-1].min()

        if last_close > recent_high:
            score, reasons = 100, ["SMC: Bullish BoS"]
        elif last_close < recent_low:
            score, reasons = -100, ["SMC: Bearish BoS"]
        elif df['low'].iloc[-1] < recent_low and last_close > recent_low:
            score, reasons = 80, ["SMC: Bullish Sweep"]
        elif df['high'].iloc[-1] > recent_high and last_close < recent_high:
            score, reasons = -80, ["SMC: Bearish Sweep"]
        return score, reasons

    def _analyze_momentum(self, df):
        if df is None or len(df) < 20: return 0, ["Mom: Insufficient Data"]
        score, reasons = 0, []
        try:
            rsi = ta.rsi(df['close'], length=14).iloc[-1]
            macd = ta.macd(df['close'])
            m_val, m_sig = macd['MACD_12_26_9'].iloc[-1], macd['MACDs_12_26_9'].iloc[-1]
            if rsi < 30: score += 40; reasons.append("RSI Oversold")
            elif rsi > 70: score -= 40; reasons.append("RSI Overbought")
            if m_val > m_sig: score += 30; reasons.append("MACD Bullish")
            else: score -= 30; reasons.append("MACD Bearish")
        except: return 0, ["Mom: Indicator Fail"]
        return score, reasons

    def _analyze_trend(self, df_1d, df_4h):
        if df_1d is None or df_4h is None: return 0, ["Trend: No Data"]
        score, reasons = 0, []
        try:
            ema200 = ta.ema(df_1d['close'], length=200).iloc[-1]
            if df_1d['close'].iloc[-1] > ema200: score += 50; reasons.append("Bullish EMA200")
            else: score -= 50; reasons.append("Bearish EMA200")
            st = ta.supertrend(df_4h['high'], df_4h['low'], df_4h['close'], length=7, multiplier=3)
            col = [c for c in st.columns if "SUPERT" in c][0]
            if st[col].iloc[-1] == 1: score += 50; reasons.append("Bullish Supertrend")
            else: score -= 50; reasons.append("Bearish Supertrend")
        except: pass
        return score, reasons

    async def generate_final_signal(self, symbol: str, whale_data=None) -> Optional[Signal]:
        df_1d, df_4h, df_15m = await self._fetch_comprehensive_data(symbol)
        if df_1d is None: return None

        smc_score, smc_reasons = self._analyze_smc(df_4h)
        trend_score, trend_reasons = self._analyze_trend(df_1d, df_4h)
        mom_score, mom_reasons = self._analyze_momentum(df_15m)
        
        inst_score, inst_reasons = 0, []
        if whale_data:
            vol = whale_data.get("total_volume", 0)
            side = whale_data.get("side", "").upper()
            if vol and vol > 1_000_000:
                inst_score = 100 if side == "BUY" else -100
                inst_reasons.append(f"Whale {side}")

        final_score = (
            (smc_score * self.WEIGHTS["SMC_STRUCTURE"]) +
            (inst_score * self.WEIGHTS["INSTITUTIONAL"]) +
            (trend_score * self.WEIGHTS["TREND_SENSE"]) +
            (mom_score * self.WEIGHTS["MOMENTUM_SENSE"])
        )

        direction = "NEUTRAL"
        if final_score >= 60: direction = "STRONG_BUY"
        elif final_score >= 30: direction = "BUY"
        elif final_score <= -60: direction = "STRONG_SELL"
        elif final_score <= -30: direction = "SELL"
        else: return None

        price = df_15m['close'].iloc[-1]
        try:
            atr_val = ta.atr(df_15m['high'], df_15m['low'], df_15m['close']).iloc[-1]
            if pd.isna(atr_val): atr_val = price * 0.01
        except: atr_val = price * 0.01

        return Signal(
            symbol=symbol, direction=direction, score=abs(final_score),
            confidence="HIGH" if abs(final_score) > 70 else "MEDIUM",
            factors=smc_reasons + trend_reasons + mom_reasons + inst_reasons,
            entry_zone=(float(price * 0.999), float(price * 1.001)),
            stop_loss=float(price - (atr_val * 2)) if "BUY" in direction else float(price + (atr_val * 2)),
            take_profit=float(price + (atr_val * 3)) if "BUY" in direction else float(price - (atr_val * 3)),
            exit_target=float(price + (atr_val * 3)) if "BUY" in direction else float(price - (atr_val * 3))
        )

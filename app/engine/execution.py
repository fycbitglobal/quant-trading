import logging
import asyncio
from typing import Dict, Optional, List, Any, Tuple
from dataclasses import dataclass
from app.clients.manager import ExchangeManager
from app.core.config import config

logger = logging.getLogger(__name__)

@dataclass
class Position:
    symbol: str
    amount: float
    entry_price: float
    stop_loss: float
    take_profit: float
    side: str
    timestamp: float
    status: str = "OPEN"
    pnl: float = 0.0

class ExecutionEngine:
    def __init__(self, exchange_manager: ExchangeManager, paper_mode: bool = True):
        self.manager = exchange_manager
        self.paper_mode = paper_mode
        self.active_positions: Dict[str, Position] = {}
        self.trade_history: List[Position] = []
        self.trailing_step = 0.005 

    async def execute_trade(self, symbol: str, side: str, amount: float,
                            stop_loss: float, take_profit: float,
                            entry_price: float = None) -> Optional[Position]:
        try:
            best_offer = await self.manager.get_best_price(symbol)
            current_price = best_offer["price"]
            exchange_name = best_offer["exchange"]
            if current_price == 0: return None
            final_entry_price = entry_price if entry_price is not None else current_price

            if self.paper_mode:
                pos = Position(symbol, amount, final_entry_price, stop_loss, take_profit, side, asyncio.get_event_loop().time())
                self.active_positions[symbol] = pos
                self.trade_history.append(pos)
                return pos

            client = self.manager.get_client(exchange_name)
            if not client: return None
            order = await client.place_order(symbol=symbol, side=side, amount=amount)
            if order is None or "error" in order: return None
            fill_price = float(order.get("price", final_entry_price))
            pos = Position(symbol, amount, fill_price, stop_loss, take_profit, side, asyncio.get_event_loop().time())
            self.active_positions[symbol] = pos
            self.trade_history.append(pos)
            return pos
        except Exception as e:
            logger.error(f"Execution Error: {e}"); return None

    async def monitor_and_close(self, symbol: str, current_price: float) -> Optional[Tuple[float, float]]:
        """
        Pozisyonu izler. Eğer kapandıysa (pnl, pnl_pct) döndürür.
        """
        if symbol not in self.active_positions:
            return None

        pos = self.active_positions[symbol]
        
        if pos.side in ["BUY", "STRONG_BUY"]:
            # Trailing Stop Güncelleme
            if current_price > pos.entry_price * (1 + self.trailing_step):
                new_sl = current_price * 0.995
                if new_sl > pos.stop_loss:
                    pos.stop_loss = new_sl

            # Kapatma Kontrolü
            if pos.stop_loss is not None and current_price <= pos.stop_loss:
                return await self.close_position(symbol, current_price, "STOP LOSS")
            elif pos.take_profit is not None and current_price >= pos.take_profit:
                return await self.close_position(symbol, current_price, "TAKE PROFIT")
        
        elif pos.side in ["SELL", "STRONG_SELL"]:
            # Trailing Stop Güncelleme
            if current_price < pos.entry_price * (1 - self.trailing_step):
                new_sl = current_price * 1.005
                if new_sl < pos.stop_loss:
                    pos.stop_loss = new_sl

            # Kapatma Kontrolü
            if pos.stop_loss is not None and current_price >= pos.stop_loss:
                return await self.close_position(symbol, current_price, "STOP LOSS")
            elif pos.take_profit is not None and current_price <= pos.take_profit:
                return await self.close_position(symbol, current_price, "TAKE PROFIT")
        
        return None

    async def close_position(self, symbol: str, price: float, reason: str) -> Tuple[float, float]:
        """
        Pozisyonu kapatır ve (PnL, PnL_Percentage) değerlerini döndürür.
        """
        pos = self.active_positions.get(symbol)
        if not pos: return 0.0, 0.0

        # PnL Hesaplama
        if pos.side in ["BUY", "STRONG_BUY"]:
            pnl = (price - pos.entry_price) * pos.amount
            pnl_pct = ((price / pos.entry_price) - 1) * 100
        else:
            pnl = (pos.entry_price - price) * pos.amount
            pnl_pct = (1 - (price / pos.entry_//_price)) * 100 # ERROR FIX
            pnl_pct = (1 - (price / pos.entry_price)) * 100

        pos.status, pos.pnl = "CLOSED", pnl

        if not self.paper_mode:
            best = await self.manager.get_best_price(symbol)
            client = self.manager.get_client(best["exchange"])
            close_side = "SELL" if pos.side in ["BUY", "STRONG_BUY"] else "BUY"
            await client.place_order(symbol, close_side, pos.amount)

        logger.info(f"🏁 CLOSED: {symbol} | {reason} | PnL: {pnl:.2f} USDT ({pnl_pct:.2f}%)")
        
        del self.active_positions[symbol]
        self.trade_history.append(pos)
        
        return pnl, pnl_pct

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

# Rich kütüphanesi Dashboard için gereklidir: pip install rich
try:
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
    from rich.text import Text
    from rich.console import Console
    HAS_RICH = True
except ImportError:
    HAS_RICH = False

from app.core.config import config
from app.core.logger import setup_logger
from app.clients.manager import ExchangeManager
from app.engine.signal import QuantAnalysisEngine
from app.engine.risk import RiskManager
from app.engine.execution import ExecutionEngine
from app.clients.telegram import TelegramClient

logger = setup_logger # CLEANED
logger = setup_logger()

class AresDashboard:
    """Terminal üzerinden anlık takip paneli sağlar."""
    def __init__(self, bot):
        self.bot = bot
        self.console = Console()
        self.recent_signals = [] # Son analiz edilenleri tutar

    def add_signal_log(self, symbol: str, score: float, direction: str):
        """Sinyal akışına yeni veri ekler."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {symbol}: {score:.1f} ({direction})"
        self.recent_signals.insert(0, log_entry)
        self.recent_signals = self.recent_signals[:10]

    def generate_layout(self) -> Layout:
        layout = Layout()
        layout.split_column(
            Layout(name="header", size=3),
            Layout(name="main", size=15),
            Layout(name="footer", size=6)
        )
        layout["main"].split_row(
            Layout(name="positions", ratio=2),
            Layout(name="feed", ratio=1)
        )
        return layout

    def update_header(self) -> Panel:
        status_text = Text(f"🚀 ARES GLOBAL QUANT | Balance: {self.bot.risk_manager.balance:.2f} USDT", 
                           style="bold cyan", justify="center")
        return Panel(status_text, title="[bold white]System Monitor[/bold white]", border_style="blue")

    def update_positions(self) -> Table:
        table = Table(title="Active Positions", expand=True, border_style="green")
        table.add_column("Symbol", style="cyan")
        table.add_column("Side", style="magenta") # CLEANED
        table.add_column("Side", style="magenta")
        table.add_column("Entry", style="white")
        table.add_column("SL", style="red")
        table.add_column("TP", style="green")
        
        for symbol, pos in self.bot.execution.active_positions.items():
            table.add_row(symbol, pos.side, f"{pos.entry_price:.2f}", f"{pos.stop_loss:.2f}", f"{pos.take_profit:.2f}")
        
        if not self.bot.execution.active_positions:
            table.add_row("No active positions", "-", "-", "-", "-")
        return table

    def update_feed(self) -> Panel:
        feed_text = "\n".join(self.recent_signals) if self.recent_signals else "Sinyal bekleniyor..."
        return Panel(Text(feed_text, style="white"), title="Sinyal Akışı", border_style="gray")

    def update_performance(self) -> Panel:
        history = self.bot.execution.trade_history
        if not history:
            return Panel(Text("Henüz tamamlanmış işlem yok.", style="white"), title="Performans", border_style="yellow")
        
        # FIX:
        if not history: return Panel(Text("No Data", style="white"), title="Perf")
        
        total_pnl = sum(pos.pnl for pos in history)
        wins = len([p for p in history if p.pnl > 0])
        win_rate = (wins / len(history)) * 100 if history else 0
        
        perf_text = Text(
            f"Total PnL: {total_pnl:.2f} USDT | Win Rate: %{win_rate:.1f} | Trades: {len(history)}",
            style="bold yellow"
        )
        return Panel(perf_text, title="Kuantitatif Performans", border_style="yellow")

class AresQuant:
    def __init__(self):
        logger.info("🚀 ARES GLOBAL QUANT | Institutional Trading Mode Starting...")
        
        self.telegram = TelegramClient(config.BOT_TOKEN)
        self.ex_manager = ExchangeManager()
        
        binance_client = self.ex_manager.get_client("BINANCE")
        self.signal_engine = QuantAnalysisEngine(binance_client)
        self.risk_manager = RiskManager(initial_balance=1000.0) 
        self.execution = ExecutionEngine(self.ex_manager)
        
        self.symbols = [
            "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", 
            "ADAUSDT", "DOGEUSDT", "AVAXUSDT", "DOTUSDT", "LINKUSDT",
            "MATICUSDT", "LTCUSDT", "SHIBUSDT", "NEARUSDT", "SUIUSDT",
            "APTUSDT", "PEPEUSDT", "OPUSDT", "ARBUSDT", "INJUSDT", 
            "FETUSDT", "RENDERUSDT", "LDOUSDT", "FILUSDT"
        ]
        
        self.signal_memory = {} 
        self.dashboard = AresDashboard(self) if HAS_RICH else None

    async def send_notification(self, msg: str):
        try:
            await self.telegram.send(config.OUTPUT_CHANNEL, msg)
        except Exception as e:
            logger.error(f"Telegram Hatası: {e}")

    async def send_trade_ticket(self, signal, pos):
        emoji = "🟢" if "BUY" in signal.direction else "🔴"
        msg = (
            f"{emoji} *ARES QUANT | POSITION OPENED* {emoji}\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 **Asset:** `{signal.symbol}`\n"
            f"↕️ **Side:** `{signal.direction}`\n"
            f"💪 **Confidence:** `{signal.confidence}` ({signal.score:.1f})\n"
            f"💰 **Amount:** `{pos.amount:.4f}`\n"
            f"📉 **Entry:** `{pos.entry_price:.2f}`\n"
            f"🛑 **Stop Loss:** `{pos.stop_loss:.2f}`\n"
            f"🎯 **Take Profit:** `{pos.take_profit:.2f}`\n\n"
            f"🧠 **Sinyal Nedenleri:**\n" + "\n".join([f"• {f}" for f in signal.factors]) + "\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🕒 {datetime.now().strftime('%H:%M:%S')}"
        )
        await self.send_notification(msg)

    async def send_close_report(self, symbol, pos, price, reason):
        pnl = (price - pos.entry_price) * pos.amount if pos.side in ["BUY", "STRONG_BUY"] else (pos.entry_price - price) * pos.amount
        pnl_pct = ((price / pos.entry_price) - 1) * 100 if pos.side in ["BUY", "STRONG_BUY"] else (1 - (price / pos.entry_price)) * 100
        emoji = "💰" if pnl > 0 else "📉"
        msg = (
            f"{emoji} *ARES QUANT | POSITION CLOSED*\n"
            f"━━━━━━━━━━━━━━━━━━━━\n"
            f"🪙 **Asset:** `{symbol}`\n"
            f"🏁 **Reason:** `{reason}`\n"
            f"📉 **Exit Price:** `{price:.2f}`\n"
            f"💵 **Net PnL:** `{pnl:.2f} USDT`\n"
            f"📊 **Return:** `%{pnl_pct:.2f}`\n"
            f"━━━━━━━━━━━━━━━━━━━━"
        )
        await self.send_notification(msg)

    async def process_symbol(self, symbol):
        try:
            best_offer = await self.ex_manager.get_best_price(symbol)
            current_price = best_offer['price']
            if current_price == 0: return

            if symbol in self.execution.active_positions:
                pos = self.execution.active_positions[symbol]
                if pos.side in ["BUY", "STRONG_BUY"]:
                    if current_price <= pos.stop_loss or current_price >= pos.take_profit:
                        reason = "STOP LOSS" if current_price <= pos.stop_loss else "TAKE PROFIT"
                        res = await self.execution.close_position(symbol, current_price, reason)
                        if res:
                            pnl, pct = res
                            await self.send_close_report(symbol, pos, current_price, reason) # FIX
                            await self.send_close_report(symbol, pos, current_price, reason) # FIX
                            await self.send_close_report(symbol, pos, current_price, reason)
                elif pos.side in ["SELL", "STRONG_SELL"]:
                    if current_price >= pos.stop_loss or current_price <= pos.take_profit:
                        reason = "STOP LOSS" if current_price >= pos.stop_loss else "TAKE PROFIT"
                        res = await self.execution.close_position(symbol, current_price, reason)
                        if res:
                            pnl, pct = res
                            await self.send_close_report(symbol, pos, current_price, reason)
                return

            signal = await self.signal_engine.generate_final_signal(symbol)
            
            # Dashboard Feed Güncellemesi
            if signal:
                self.dashboard.add_signal_log(symbol, signal.score, signal.direction)
            else:
                self.dashboard.add_signal_log(symbol, 0.0, "NEUTRAL")

            if signal and signal.direction in ["BUY", "STRONG_BUY", "SELL", "STRONG_SELL"]:
                last_signal = self.signal_memory.get(symbol)
                if last_signal == signal.direction: return
                self.signal_memory[symbol] = signal.direction # CLEANED
                self.signal_memory[symbol] = signal.direction

                if signal.score >= 30:
                    amount = self.risk_manager.calculate_position_size(current_price, signal.stop_loss)
                    if amount > 0:
                        pos = await self.execution.execute_trade(
                            symbol=symbol, side=signal.direction, amount=amount,
                            stop_loss=signal.stop_loss, take_profit=signal.take_profit,
                            entry_price=current_price
                        )
                        if pos: await self.send_trade_ticket(signal, pos)

        except Exception as e:
            logger.error(f"Süreç hatası ({symbol}): {e}")

    async def run(self):
        logger.info(f"🚀 {len(self.symbols)} varlık aktif olarak taranıyor...")
        if not HAS_RICH:
            while True:
                try:
                    tasks = [self.process_symbol(symbol) for symbol in self.symbols]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(60)
                except Exception as e:
                    logger.error(f"Global Loop Hatası: {e}")
                    await asyncio.sleep(10)
            return

        with Live(self.dashboard.generate_layout(), refresh_per_second=1) as live:
            while True:
                try:
                    layout = self.dashboard.generate_layout()
                    layout["header"].update(self.dashboard.update_header())
                    layout["main"]["positions"].update(self.dashboard.update_positions())
                    layout["main"]["feed"].update(self.dashboard.update_feed())
                    layout["footer"].update(self.dashboard.update_performance())
                    live.update(layout)
                    
                    tasks = [self.process_symbol(symbol) for symbol in self.symbols]
                    await asyncio.gather(*tasks)
                    await asyncio.sleep(60) 

                except Exception as e:
                    logger.error(f"Global Loop Hatası: {e}")
                    await asyncio.sleep(10)

if __name__ == "__main__":
    bot = AresQuant()
    try:
        asyncio.run(bot.run())
    except KeyboardInterrupt:
        logger.info("🛑 Bot kapatıldı.")

import logging
from datetime import datetime
from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.live import Live

logger = logging.getLogger(__name__)

class AresDashboard:
    def __init__(self, bot):
        self.bot = bot
        self.console = Console()
        self.recent_signals = [] # Son analiz edilen coinleri tutar

    def add_signal_log(self, symbol: str, score: float, direction: str):
        """Sinyal akışına yeni veri ekler."""
        timestamp = datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {symbol}: {score:.1f} ({direction})"
        self.recent_signals.insert(0, log_entry)
        self.recent_signals = self.recent_signals[:10] # Sadece son 10 kaydı tut

    def _calculate_sentiment(self) -> str:
        """Tüm takip edilen varlıkların ortalama puanına göre piyasa yönünü belirler."""
        # Sinyal hafızasındaki son puanları topla
        scores = [s for s in self.bot.signal_memory.values() if isinstance(s, float)]
        if not scores: return "NEUTRAL"
        
        avg = sum(scores) / len(scores)
        if avg > 40: return "🐂 BULLISH"
        if avg < -40: return "🐻 BEARISH"
        return "⚖️ NEUTRAL"

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
        sentiment = self._calculate_sentiment()
        status_text = Text(
            f"🚀 ARES GLOBAL QUANT | Balance: {self.bot.risk_manager.balance:.2f} USDT | Sentiment: {sentiment}", 
            style="bold cyan", justify="center"
        )
        return Panel(status_text, title="[bold white]SISTEM MONITORU[/bold white]", border_style="blue")

    def update_positions(self) -> Table:
        table = Table(title="Sinyalized Pozisyonlar", expand=True, border_style="green")
        table.add_column("Coin", style="cyan")
        table.add_column("Yön", style="magenta")
        table.add_column("Giriş", style="white")
        table.add_column("SL", style="red")
        table.add_column("TP", style="green")
        
        for symbol, pos in self.bot.execution.active_positions.items():
            table.add_row(symbol, pos.side, f"{pos.entry_price:.2f}", f"{pos.stop_loss:.2f}", f"{pos.take_profit:.2f}")
        
        if not self.bot.execution.active_positions:
            table.add_row("Aktif pozisyon yok", "-", "-", "-", "-")
        return table

    def update_feed(self) -> Panel:
        feed_text = "\n".join(self.recent_signals) if self.recent_signals else "Sinyal bekleniyor..."
        return Panel(Text(feed_text, style="white"), title="Sinyal Akışı", border_style="gray")

    def update_performance(self) -> Panel:
        history = self.bot.execution.trade_history
        if not history:
            return Panel(Text("Henüz tamamlanmış işlem yok.", style="white"), title="Performans", border_style="yellow")
        
        total_pnl = sum(pos.pnl for pos in history)
        wins = len([p for p in history if p.pnl > 0])
        win_rate = (wins / len(history)) * 100 if history else 0
        
        perf_text = Text(
            f"Toplam PnL: {total_pnl:.2f} USDT | Win Rate: %{win_rate:.1f} | İşlem Sayısı: {len(history)}",
            style="bold yellow"
        )
        return Panel(perf_text, title="Kuantitatif Performans", border_style="yellow")

    async def update_dashboard(self, live: Live):
        layout = self.generate_layout()
        layout["header"].update(self.update_header())
        layout["main"].update_positions = self.update_positions() # Not: Layout update sistemi farklıdır
        layout["main"]["positions"].update(self.update_positions())
        layout["main"]["feed"].update(self.update_feed())
        layout["footer"].update(self.update_performance())
        await live.update(layout)

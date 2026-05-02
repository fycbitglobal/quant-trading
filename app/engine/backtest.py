class BacktestEngine:

    def __init__(self):
        self.trades = []

    def run(self, historical_data, strategy_fn):
        balance = 1000

        for candle in historical_data:
            signal = strategy_fn(candle)

            if signal["direction"] == "BUY":
                entry = candle["close"]
                exit_price = candle["close"] * 1.01

                pnl = (exit_price - entry)
                balance += pnl

                self.trades.append(pnl)

        return {
            "final_balance": balance,
            "trades": len(self.trades),
            "winrate": len([t for t in self.trades if t > 0]) / len(self.trades) * 100
        }
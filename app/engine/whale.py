class WhaleDetector:
    def detect_whale_activity(self, trades: list):
        large_trades = [t for t in trades if t["qty"] > 100000]

        if len(large_trades) > 3:
            return "WHALE_ACCUMULATION"
        if len(large_trades) > 6:
            return "WHALE_DISTRIBUTION"

        return "NORMAL"
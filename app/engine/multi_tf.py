class MultiTimeframeConfirm:
    def confirm(self, tf_signals: dict):
        """
        tf_signals = {
            "1m": "BUY",
            "5m": "BUY",
            "15m": "SELL"
        }
        """

        buys = sum(1 for v in tf_signals.values() if "BUY" in v)
        sells = sum(1 for v in tf_signals.values() if "SELL" in v)

        if buys >= 2:
            return "BULL_CONFIRMED"
        if sells >= 2:
            return "BEAR_CONFIRMED"

        return "NO_CONFIRMATION"
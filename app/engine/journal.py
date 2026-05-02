import numpy as np

class SmartRisk:

    def calculate_kelly(self, winrate, rr):
        winrate = winrate / 100
        return max(0.01, winrate - ((1 - winrate) / rr))

    def position_size(self, balance, risk_pct, volatility):
        base = balance * risk_pct
        adjusted = base / (volatility + 1e-6)
        return max(0, adjusted)
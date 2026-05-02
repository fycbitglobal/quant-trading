import numpy as np

class AISignalFusion:

    def __init__(self):
        self.weights = {
            "smc": 0.30,
            "momentum": 0.25,
            "trend": 0.25,
            "orderflow": 0.20
        }

    def fuse(self, smc, momentum, trend, orderflow):
        score = (
            smc * self.weights["smc"] +
            momentum * self.weights["momentum"] +
            trend * self.weights["trend"] +
            orderflow * self.weights["orderflow"]
        )

        confidence = min(100, abs(score))

        direction = "BUY" if score > 10 else "SELL" if score < -10 else "NEUTRAL"

        return {
            "score": float(score),
            "confidence": float(confidence),
            "direction": direction
        }
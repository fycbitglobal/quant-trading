class RiskManager:

    def __init__(self, max_risk=0.01):
        self.max_risk = max_risk

    def validate(self, order, portfolio):
        if portfolio.exposure > 0.1:
            return False
        return True

class AISignalWeight:
    def weight(self, base_score, orderflow, smc, whale, mtf):
        score = base_score

        if smc == "BULLISH_SWEEP":
            score += 10
        if smc == "BEARISH_SWEEP":
            score -= 10

        if whale == "WHALE_ACCUMULATION":
            score += 15
        if whale == "WHALE_DISTRIBUTION":
            score -= 15

        if mtf == "BULL_CONFIRMED":
            score += 20
        if mtf == "BEAR_CONFIRMED":
            score -= 20

        score += orderflow * 0.5

        return score
class Event: pass

class MarketEvent(Event):
    def __init__(self, symbol, price, volume):
        self.symbol = symbol
        self.price = price

class SignalEvent(Event):
    def __init__(self, symbol, signal):
        self.symbol = symbol
        self.signal = signal

class OrderEvent(Event):
    def __init__(self, symbol, side, qty):
        self.symbol = symbol
        self.side = side
        self.qty = qty

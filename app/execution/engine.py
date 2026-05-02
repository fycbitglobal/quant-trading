class ExecutionEngine:

    def __init__(self, client):
        self.client = client

    async def execute(self, order_event):
        await self.client.place_order(
            order_event.symbol,
            order_event.side,
            order_event.qty
        )

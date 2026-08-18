from app.services.nexon_client import NexonClient


class TradeService:

    def __init__(self, nexon_client: NexonClient):
        self.nexon_client = nexon_client

    async def get_trades(
        self,
        ouid: str,
        tradetype: str,
    ):
        return await self.nexon_client.get_trade_history(
            ouid,
            tradetype,
        )

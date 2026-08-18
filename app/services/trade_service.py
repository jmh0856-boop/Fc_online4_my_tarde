from app.services.nexon_client import NexonClient
from app.services.player_service import PlayerService


class TradeService:

    def __init__(
        self,
        nexon_client: NexonClient,
        player_service: PlayerService,
    ):
        self.nexon_client = nexon_client
        self.player_service = player_service

    async def get_trades(
        self,
        ouid: str,
        trade_type: str,
        page: int = 1,
        size: int = 20,
    ):
        if trade_type == "all":
            buy_trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="buy",
            )

            sell_trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="sell",
            )

            trades = [
                *[
                    {**trade, "trade_type": "buy"}
                    for trade in buy_trades
                ],
                *[
                    {**trade, "trade_type": "sell"}
                    for trade in sell_trades
                ],
            ]

        else:
            trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type=trade_type,
            )

            trades = [
                {**trade, "trade_type": trade_type}
                for trade in trades
            ]

        result = []

        for trade in trades:
            player_info = await self.player_service.get_player_info(
                trade["spid"]
            )

            result.append(
                {
                    "trade_type": trade["trade_type"],
                    "trade_date": trade["tradeDate"],
                    "sale_sn": trade["saleSn"],
                    "spid": trade["spid"],
                    "player_name": player_info["player_name"],
                    "season_id": player_info["season_id"],
                    "season_name": player_info["season_name"],
                    "season_img": player_info["season_img"],
                    "grade": trade["grade"],
                    "value": trade["value"],
                }
            )

        result.sort(
            key=lambda trade: trade["trade_date"],
            reverse=True,
        )

        total = len(result)

        start = (page - 1) * size
        end = start + size

        items = result[start:end]

        return {
            "items": items,
            "page": page,
            "size": size,
            "total": total,
            "has_next": end < total,
        }
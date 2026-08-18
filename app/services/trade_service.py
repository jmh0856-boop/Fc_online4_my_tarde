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
        page: int,
        size: int,
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
                {
                    **trade,
                    "trade_type": "buy",
                }
                for trade in buy_trades
            ]

            trades += [
                {
                    **trade,
                    "trade_type": "sell",
                }
                for trade in sell_trades
            ]

        else:
            raw_trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type=trade_type,
            )

            trades = [
                {
                    **trade,
                    "trade_type": trade_type,
                }
                for trade in raw_trades
            ]

        result = []

        for trade in trades:
            player_info = await self.player_service.get_player_info(
                trade["spid"]
            )

            if player_info is None:
                continue

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
                    "player_img": player_info["player_img"],
                    "grade": trade["grade"],
                    "value": trade["value"],
                }
            )

        # 최신순
        result.sort(
            key=lambda x: x["trade_date"],
            reverse=True,
        )

        total = len(result)

        start = (page - 1) * size
        end = start + size

        return {
            "items": result[start:end],
            "page": page,
            "size": size,
            "total": total,
            "has_next": end < total,
        }
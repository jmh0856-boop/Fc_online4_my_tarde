from datetime import datetime, timedelta

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
        size: int = 10,
        start_date: str | None = None,
        end_date: str | None = None,
    ):

        # =========================================================
        # 1. 조회할 거래 종류 결정
        # =========================================================

        trades = []

        # 전체
        if trade_type == "all":

            buy_data = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="buy",
                offset=0,
                limit=100,
            )

            sell_data = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="sell",
                offset=0,
                limit=100,
            )

            # Nexon API가 list를 반환하므로 그대로 사용
            buy_trades = (
                buy_data
                if isinstance(buy_data, list)
                else buy_data.get("items", [])
            )

            sell_trades = (
                sell_data
                if isinstance(sell_data, list)
                else sell_data.get("items", [])
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

        # 구매
        elif trade_type == "buy":

            raw_data = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="buy",
                offset=0,
                limit=100,
            )

            raw_trades = (
                raw_data
                if isinstance(raw_data, list)
                else raw_data.get("items", [])
            )

            trades = [
                {
                    **trade,
                    "trade_type": "buy",
                }
                for trade in raw_trades
            ]

        # 판매
        elif trade_type == "sell":

            raw_data = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="sell",
                offset=0,
                limit=100,
            )

            raw_trades = (
                raw_data
                if isinstance(raw_data, list)
                else raw_data.get("items", [])
            )

            trades = [
                {
                    **trade,
                    "trade_type": "sell",
                }
                for trade in raw_trades
            ]

        else:
            trades = []


        # =========================================================
        # 2. 날짜 필터
        # =========================================================

        if start_date:

            start_datetime = datetime.fromisoformat(
                start_date
            )

            filtered_trades = []

            for trade in trades:

                trade_date = datetime.fromisoformat(
                    trade["tradeDate"]
                )

                if trade_date >= start_datetime:
                    filtered_trades.append(trade)

            trades = filtered_trades


        if end_date:

            end_datetime = (
                datetime.fromisoformat(end_date)
                + timedelta(days=1)
            )

            filtered_trades = []

            for trade in trades:

                trade_date = datetime.fromisoformat(
                    trade["tradeDate"]
                )

                if trade_date < end_datetime:
                    filtered_trades.append(trade)

            trades = filtered_trades


        # =========================================================
        # 3. 최신 거래순 정렬
        # =========================================================

        trades.sort(
            key=lambda trade: trade["tradeDate"],
            reverse=True,
        )


        # =========================================================
        # 4. 선수 정보 붙이기
        # =========================================================

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


        # =========================================================
        # 5. 페이지네이션
        # =========================================================

        total = len(result)

        start = (page - 1) * size
        end = start + size

        items = result[start:end]


        # =========================================================
        # 6. 응답
        # =========================================================

        return {
            "items": items,
            "page": page,
            "size": size,
            "total": total,
            "has_next": end < total,
        }
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
        size: int = 20,
        start_date: str | None = None,
        end_date: str | None = None,
    ):

        # ==========================================
        # 페이지 계산
        # ==========================================

        offset = (page - 1) * size
        limit = size

        # ==========================================
        # 거래내역 조회
        # ==========================================

        if trade_type == "all":

            buy_trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="buy",
                offset=offset,
                limit=limit,
            )

            sell_trades = await self.nexon_client.get_trade_history(
                ouid=ouid,
                trade_type="sell",
                offset=offset,
                limit=limit,
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
                offset=offset,
                limit=limit,
            )

            trades = [
                {
                    **trade,
                    "trade_type": trade_type,
                }
                for trade in raw_trades
            ]

        # ==========================================
        # 날짜 필터
        # ==========================================

        if start_date:

            start_datetime = datetime.fromisoformat(
                start_date
            )

            trades = [
                trade
                for trade in trades
                if datetime.fromisoformat(
                    trade["tradeDate"]
                ) >= start_datetime
            ]

        if end_date:

            end_datetime = (
                datetime.fromisoformat(end_date)
                + timedelta(days=1)
            )

            trades = [
                trade
                for trade in trades
                if datetime.fromisoformat(
                    trade["tradeDate"]
                ) < end_datetime
            ]

        # ==========================================
        # 최신순 정렬
        # ==========================================

        trades.sort(
            key=lambda x: x["tradeDate"],
            reverse=True,
        )

        # ==========================================
        # 선수 정보 추가
        # ==========================================

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

        # ==========================================
        # 결과 페이지네이션
        # ==========================================

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
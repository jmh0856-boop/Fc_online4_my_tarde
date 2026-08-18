from datetime import datetime
from typing import Any

from app.services.nexon_client import NexonClient


class TradeService:
    """FC Online 거래 내역 서비스."""

    def __init__(
        self,
        nexon_client: NexonClient,
    ) -> None:
        self.nexon_client = nexon_client

        # SPID → 선수명
        self.player_map: dict[int, str] = {}

        # 시즌 ID → 시즌 정보
        self.season_map: dict[int, dict[str, Any]] = {}

    # =========================================================
    # 메타데이터
    # =========================================================

    def load_player_metadata(self) -> None:
        """선수 메타데이터를 불러온다."""

        players = self.nexon_client.get_player_metadata()

        self.player_map.clear()

        for player in players:
            spid = player.get("id")
            name = player.get("name")

            if spid is None or not name:
                continue

            self.player_map[int(spid)] = str(name)

    def load_season_metadata(self) -> None:
        """시즌 메타데이터를 불러온다."""

        seasons = self.nexon_client.get_season_metadata()

        self.season_map.clear()

        for season in seasons:
            season_id = season.get("seasonId")

            if season_id is None:
                continue

            self.season_map[int(season_id)] = season

    def load_metadata(self) -> None:
        """선수 + 시즌 메타데이터를 모두 불러온다."""

        if not self.player_map:
            self.load_player_metadata()

        if not self.season_map:
            self.load_season_metadata()

    # =========================================================
    # 선수 / 시즌
    # =========================================================

    def get_player_name(
        self,
        spid: int | None,
    ) -> str:
        """SPID로 선수명을 조회한다."""

        if spid is None:
            return "알 수 없는 선수"

        return self.player_map.get(
            int(spid),
            "알 수 없는 선수",
        )

    def get_season_info(
        self,
        spid: int | None,
    ) -> dict[str, Any]:
        """SPID로 시즌 정보를 조회한다."""

        if spid is None:
            return {
                "season_id": None,
                "season_name": "알 수 없는 시즌",
                "season_img": None,
            }

        spid = int(spid)

        # SPID의 앞자리에서 시즌 ID 추출
        season_id = spid // 1_000_000

        season = self.season_map.get(season_id)

        if season is None:
            return {
                "season_id": season_id,
                "season_name": "알 수 없는 시즌",
                "season_img": None,
            }

        return {
            "season_id": season_id,
            "season_name": season.get(
                "className",
                "알 수 없는 시즌",
            ),
            "season_img": season.get(
                "seasonImg"
            ),
        }

    # =========================================================
    # 거래 데이터 변환
    # =========================================================

    def _normalize_trade(
        self,
        trade: dict[str, Any],
        trade_type: str,
    ) -> dict[str, Any]:
        """NEXON 거래 데이터를 프로그램 내부 형식으로 변환한다."""

        spid = trade.get("spid")

        season_info = self.get_season_info(spid)

        return {
            "trade_type": trade_type,

            "trade_date": trade.get(
                "tradeDate"
            ),

            # 내부적으로는 필요할 수 있으므로 보관하지만
            # UI에서는 표시하지 않는다.
            "sale_sn": trade.get(
                "saleSn"
            ),

            "spid": spid,

            "player_name": self.get_player_name(
                spid
            ),

            "season_id": season_info.get(
                "season_id"
            ),

            "season_name": season_info.get(
                "season_name"
            ),

            "season_img": season_info.get(
                "season_img"
            ),

            "grade": trade.get(
                "grade"
            ),

            "value": trade.get(
                "value"
            ),
        }

    # =========================================================
    # 거래 조회
    # =========================================================

    def get_buy_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """구매 거래 내역을 조회한다."""

        self.load_metadata()

        trades = self.nexon_client.get_trade_history(
            "buy",
            offset,
            limit,
        )

        return [
            self._normalize_trade(
                trade,
                "구매",
            )
            for trade in trades
        ]

    def get_sell_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """판매 거래 내역을 조회한다."""

        self.load_metadata()

        trades = self.nexon_client.get_trade_history(
            "sell",
            offset,
            limit,
        )

        return [
            self._normalize_trade(
                trade,
                "판매",
            )
            for trade in trades
        ]

    def get_all_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """구매 + 판매 거래 내역을 조회한다."""

        self.load_metadata()

        buy_trades = self.get_buy_history(
            offset,
            limit,
        )

        sell_trades = self.get_sell_history(
            offset,
            limit,
        )

        trades = buy_trades + sell_trades

        trades.sort(
            key=lambda trade: (
                trade.get("trade_date") or ""
            ),
            reverse=True,
        )

        return trades

    # =========================================================
    # 표시용 포맷
    # =========================================================

    @staticmethod
    def format_price(
        value: int | float | None,
    ) -> str:
        """BP 금액을 보기 좋은 조 단위로 표시한다."""

        if value is None:
            return "-"

        value = int(value)

        # 1조 이상
        if value >= 1_000_000_000_000:
            jo = value / 1_000_000_000_000
            return f"{jo:.2f}조"

        # 1억 이상
        if value >= 100_000_000:
            eok = value / 100_000_000
            return f"{eok:.2f}억"

        return f"{value:,}"

    @staticmethod
    def format_date(
        trade_date: str | None,
    ) -> str:
        """거래일시를 화면 표시용으로 변환한다."""

        if not trade_date:
            return "-"

        try:
            dt = datetime.fromisoformat(
                trade_date
            )

            return dt.strftime(
                "%Y-%m-%d %H:%M"
            )

        except (ValueError, TypeError):
            return str(trade_date)

    # =========================================================
    # 통계
    # =========================================================

    def calculate_statistics(
        self,
        trades: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """거래 내역 통계를 계산한다."""

        buy_trades = [
            trade
            for trade in trades
            if trade.get("trade_type") == "구매"
        ]

        sell_trades = [
            trade
            for trade in trades
            if trade.get("trade_type") == "판매"
        ]

        buy_amount = sum(
            int(trade.get("value") or 0)
            for trade in buy_trades
        )

        sell_amount = sum(
            int(trade.get("value") or 0)
            for trade in sell_trades
        )

        return {
            "total_count": len(trades),
            "buy_count": len(buy_trades),
            "sell_count": len(sell_trades),
            "buy_amount": buy_amount,
            "sell_amount": sell_amount,
            "difference": sell_amount - buy_amount,
        }
from datetime import datetime
from typing import Any

from app.services.nexon_client import (
    NexonAPIError,
    NexonClient,
)


class TradeService:
    """FC Online 거래 내역 서비스."""

    def __init__(
        self,
        nexon_client: NexonClient,
    ) -> None:
        self.nexon_client = nexon_client

        # =====================================================
        # 메타데이터
        # =====================================================

        # SPID → 선수명
        self.player_map: dict[int, str] = {}

        # 시즌 ID → 시즌 정보
        self.season_map: dict[
            int,
            dict[str, Any],
        ] = {}

        # =====================================================
        # 현재가 캐시
        # =====================================================

        # key:
        #     (spid, grade, n8_index)
        #
        # value:
        #     현재가
        self.price_cache: dict[
            tuple[int, int, int],
            int | None,
        ] = {}

    # =========================================================
    # 메타데이터
    # =========================================================

    def load_player_metadata(self) -> None:
        """선수 메타데이터를 불러온다."""

        players = (
            self.nexon_client
            .get_player_metadata()
        )

        self.player_map.clear()

        for player in players:
            spid = player.get(
                "id"
            )

            name = player.get(
                "name"
            )

            if spid is None or not name:
                continue

            try:
                self.player_map[
                    int(spid)
                ] = str(name)

            except (
                TypeError,
                ValueError,
            ):
                continue

    def load_season_metadata(self) -> None:
        """시즌 메타데이터를 불러온다."""

        seasons = (
            self.nexon_client
            .get_season_metadata()
        )

        self.season_map.clear()

        for season in seasons:
            season_id = season.get(
                "seasonId"
            )

            if season_id is None:
                continue

            try:
                self.season_map[
                    int(season_id)
                ] = season

            except (
                TypeError,
                ValueError,
            ):
                continue

    def load_metadata(self) -> None:
        """선수 + 시즌 메타데이터를 모두 불러온다."""

        if not self.player_map:
            self.load_player_metadata()

        if not self.season_map:
            self.load_season_metadata()

    # =========================================================
    # 선수
    # =========================================================

    def get_player_name(
        self,
        spid: int | None,
    ) -> str:
        """SPID로 선수명을 조회한다."""

        if spid is None:
            return "알 수 없는 선수"

        try:
            spid = int(
                spid
            )

        except (
            TypeError,
            ValueError,
        ):
            return "알 수 없는 선수"

        return self.player_map.get(
            spid,
            "알 수 없는 선수",
        )

    # =========================================================
    # 시즌
    # =========================================================

    def get_season_info(
        self,
        spid: int | None,
    ) -> dict[str, Any]:
        """SPID로 시즌 정보를 조회한다."""

        default_result = {
            "season_id": None,
            "season_name": "알 수 없는 시즌",
            "season_img": None,
        }

        if spid is None:
            return default_result

        try:
            spid = int(
                spid
            )

        except (
            TypeError,
            ValueError,
        ):
            return default_result

        # SPID 앞자리에서 시즌 ID 추출
        season_id = (
            spid // 1_000_000
        )

        season = self.season_map.get(
            season_id
        )

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
    # 데이터센터 가격 파싱
    # =========================================================

    @staticmethod
    def _parse_price_list(
        value: Any,
    ) -> list[int]:
        """
        데이터센터 eachPrice를 강화별 가격 리스트로 변환한다.

        대응 형식:

        list
            [0, 100, 200, ...]

        문자열
            "0|100|200|..."

        또는

            "0,100,200,..."
        """

        if isinstance(
            value,
            list,
        ):
            result: list[int] = []

            for item in value:
                try:
                    result.append(
                        int(
                            item or 0
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    result.append(0)

            return result

        if isinstance(
            value,
            str,
        ):
            raw = value.strip()

            if not raw:
                return []

            if "|" in raw:
                parts = raw.split(
                    "|"
                )

            elif "," in raw:
                parts = raw.split(
                    ","
                )

            else:
                parts = [
                    raw
                ]

            result: list[int] = []

            for item in parts:
                try:
                    result.append(
                        int(
                            item.strip()
                            or 0
                        )
                    )

                except (
                    TypeError,
                    ValueError,
                ):
                    result.append(0)

            return result

        return []

    @classmethod
    def _extract_current_price(
        cls,
        result: dict[str, Any],
        grade: int,
    ) -> int | None:
        """데이터센터 응답에서 강화별 현재가를 추출한다."""

        if grade < 0:
            return None

        # -----------------------------------------------------
        # 일반적인 응답
        # -----------------------------------------------------

        each_price = result.get(
            "eachPrice"
        )

        prices = (
            cls._parse_price_list(
                each_price
            )
        )

        if prices:
            if grade < len(
                prices
            ):
                price = prices[
                    grade
                ]

                if price > 0:
                    return price

        # -----------------------------------------------------
        # 혹시 eachPrice가 다른 형태로 내려오는 경우
        # -----------------------------------------------------

        for key in (
            "each_price",
            "EachPrice",
            "eachPrices",
        ):
            value = result.get(
                key
            )

            prices = (
                cls._parse_price_list(
                    value
                )
            )

            if not prices:
                continue

            if grade >= len(
                prices
            ):
                continue

            price = prices[
                grade
            ]

            if price > 0:
                return price

        return None

    # =========================================================
    # 현재가
    # =========================================================

    def get_current_price(
        self,
        spid: int | None,
        grade: int | None,
        n8_index: int | None = None,
    ) -> int | None:
        """
        데이터센터 기준 현재가를 조회한다.

        거래 데이터에 들어있는 n8Index를 사용한다.

        동일한 선수/강화/n8Index는 캐시한다.
        """

        # -----------------------------------------------------
        # 기본값 확인
        # -----------------------------------------------------

        if (
            spid is None
            or grade is None
        ):
            return None

        try:
            spid = int(
                spid
            )

            grade = int(
                grade
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if grade < 0:
            return None

        # -----------------------------------------------------
        # n8Index 확인
        # -----------------------------------------------------

        if n8_index is None:
            return None

        try:
            n8_index = int(
                n8_index
            )

        except (
            TypeError,
            ValueError,
        ):
            return None

        if n8_index <= 0:
            return None

        # -----------------------------------------------------
        # 캐시 확인
        # -----------------------------------------------------

        cache_key = (
            spid,
            grade,
            n8_index,
        )

        if cache_key in self.price_cache:
            return self.price_cache[
                cache_key
            ]

        # -----------------------------------------------------
        # 데이터센터 조회
        # -----------------------------------------------------

        try:
            result = (
                self.nexon_client
                .get_squad_info(
                    n8_index
                )
            )

        except (
            NexonAPIError,
            ValueError,
        ):
            self.price_cache[
                cache_key
            ] = None

            return None

        # -----------------------------------------------------
        # 응답 확인
        # -----------------------------------------------------

        if not isinstance(
            result,
            dict,
        ):
            self.price_cache[
                cache_key
            ] = None

            return None

        # -----------------------------------------------------
        # 현재가 추출
        # -----------------------------------------------------

        price = (
            self._extract_current_price(
                result,
                grade,
            )
        )

        # -----------------------------------------------------
        # 캐시 저장
        # -----------------------------------------------------

        self.price_cache[
            cache_key
        ] = price

        return price

    # =========================================================
    # 현재가 캐시 초기화
    # =========================================================

    def clear_price_cache(
        self,
    ) -> None:
        """현재가 캐시를 완전히 초기화한다."""

        self.price_cache.clear()

    # =========================================================
    # 거래 데이터 변환
    # =========================================================

    def _normalize_trade(
        self,
        trade: dict[str, Any],
        trade_type: str,
    ) -> dict[str, Any]:
        """NEXON 거래 데이터를 내부 형식으로 변환한다."""

        # -----------------------------------------------------
        # 선수
        # -----------------------------------------------------

        spid = trade.get(
            "spid"
        )

        season_info = (
            self.get_season_info(
                spid
            )
        )

        # -----------------------------------------------------
        # 강화
        # -----------------------------------------------------

        grade = trade.get(
            "grade"
        )

        try:
            grade = int(
                grade
            )

        except (
            TypeError,
            ValueError,
        ):
            grade = 0

        # -----------------------------------------------------
        # 거래금액
        # -----------------------------------------------------

        value = trade.get(
            "value"
        )

        try:
            value = int(
                value or 0
            )

        except (
            TypeError,
            ValueError,
        ):
            value = 0

        # -----------------------------------------------------
        # n8Index
        # -----------------------------------------------------

        n8_index = trade.get(
            "n8Index"
        )

        if n8_index is None:
            n8_index = trade.get(
                "n8_index"
            )

        try:
            if n8_index is not None:
                n8_index = int(
                    n8_index
                )

                if n8_index <= 0:
                    n8_index = None

        except (
            TypeError,
            ValueError,
        ):
            n8_index = None

        # -----------------------------------------------------
        # 구매가
        # -----------------------------------------------------

        buy_price = None

        if trade_type == "구매":
            buy_price = value

        # -----------------------------------------------------
        # 판매가
        # -----------------------------------------------------

        sell_price = None

        if trade_type == "판매":
            sell_price = value

        return {
            # =================================================
            # 거래 기본정보
            # =================================================

            "trade_type": trade_type,

            "trade_date": trade.get(
                "tradeDate"
            ),

            "sale_sn": trade.get(
                "saleSn"
            ),

            # =================================================
            # 선수
            # =================================================

            "spid": spid,

            "player_name": (
                self.get_player_name(
                    spid
                )
            ),

            # =================================================
            # 시즌
            # =================================================

            "season_id": (
                season_info.get(
                    "season_id"
                )
            ),

            "season_name": (
                season_info.get(
                    "season_name"
                )
            ),

            "season_img": (
                season_info.get(
                    "season_img"
                )
            ),

            # =================================================
            # 강화
            # =================================================

            "grade": grade,

            # =================================================
            # 기존 거래금액
            # =================================================

            "value": value,

            # =================================================
            # 가격
            # =================================================

            "buy_price": buy_price,

            "sell_price": sell_price,

            "current_price": None,

            "difference": None,

            # 구매 후 아직 판매되지 않은 거래
            "is_unsold": (
                trade_type == "구매"
            ),

            # =================================================
            # 데이터센터 조회용
            # =================================================

            "n8_index": n8_index,
        }

    # =========================================================
    # 차액 계산
    # =========================================================

    @staticmethod
    def calculate_difference(
        trade: dict[str, Any],
    ) -> int | None:
        """
        거래별 차액을 계산한다.

        구매:
            현재가 - 구매가

        판매:
            판매가 - 구매가
        """

        trade_type = trade.get(
            "trade_type"
        )

        buy_price = trade.get(
            "buy_price"
        )

        sell_price = trade.get(
            "sell_price"
        )

        current_price = trade.get(
            "current_price"
        )

        try:
            # -------------------------------------------------
            # 구매
            # -------------------------------------------------

            if trade_type == "구매":

                if (
                    buy_price is None
                    or current_price is None
                ):
                    return None

                return (
                    int(
                        current_price
                    )
                    - int(
                        buy_price
                    )
                )

            # -------------------------------------------------
            # 판매
            # -------------------------------------------------

            if trade_type == "판매":

                if (
                    buy_price is None
                    or sell_price is None
                ):
                    return None

                return (
                    int(
                        sell_price
                    )
                    - int(
                        buy_price
                    )
                )

        except (
            TypeError,
            ValueError,
        ):
            return None

        return None

    # =========================================================
    # 현재가 적용
    # =========================================================

    def apply_current_price(
        self,
        trade: dict[str, Any],
    ) -> dict[str, Any]:
        """거래 하나에 현재가와 차액을 적용한다."""

        current_price = (
            self.get_current_price(
                spid=trade.get(
                    "spid"
                ),
                grade=trade.get(
                    "grade"
                ),
                n8_index=trade.get(
                    "n8_index"
                ),
            )
        )

        trade[
            "current_price"
        ] = current_price

        trade[
            "difference"
        ] = self.calculate_difference(
            trade
        )

        return trade

    # =========================================================
    # 구매 내역
    # =========================================================

    def get_buy_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """구매 거래 내역을 조회한다."""

        self.load_metadata()

        trades = (
            self.nexon_client
            .get_trade_history(
                "buy",
                offset,
                limit,
            )
        )

        normalized_trades = [
            self._normalize_trade(
                trade,
                "구매",
            )
            for trade in trades
        ]

        return [
            self.apply_current_price(
                trade
            )
            for trade in normalized_trades
        ]

    # =========================================================
    # 판매 내역
    # =========================================================

    def get_sell_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """판매 거래 내역을 조회한다."""

        self.load_metadata()

        trades = (
            self.nexon_client
            .get_trade_history(
                "sell",
                offset,
                limit,
            )
        )

        normalized_trades = [
            self._normalize_trade(
                trade,
                "판매",
            )
            for trade in trades
        ]

        return [
            self.apply_current_price(
                trade
            )
            for trade in normalized_trades
        ]

    # =========================================================
    # 전체 내역
    # =========================================================

    def get_all_history(
        self,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """구매 + 판매 거래 내역을 조회한다."""

        self.load_metadata()

        buy_trades = (
            self.get_buy_history(
                offset,
                limit,
            )
        )

        sell_trades = (
            self.get_sell_history(
                offset,
                limit,
            )
        )

        trades = (
            buy_trades
            + sell_trades
        )

        trades.sort(
            key=lambda trade: (
                trade.get(
                    "trade_date"
                )
                or ""
            ),
            reverse=True,
        )

        return trades

    # =========================================================
    # 금액 표시
    # =========================================================

    @staticmethod
    def format_price(
        value: int | float | None,
    ) -> str:
        """BP 금액을 보기 좋은 단위로 표시한다."""

        if value is None:
            return "-"

        try:
            value = int(
                value
            )

        except (
            TypeError,
            ValueError,
        ):
            return "-"

        if value == 0:
            return "0"

        # -----------------------------------------------------
        # 조
        # -----------------------------------------------------

        if value >= 1_000_000_000_000:
            jo = (
                value
                / 1_000_000_000_000
            )

            return f"{jo:,.2f}조"

        # -----------------------------------------------------
        # 억
        # -----------------------------------------------------

        if value >= 100_000_000:
            eok = (
                value
                / 100_000_000
            )

            return f"{eok:,.2f}억"

        return f"{value:,}"

    # =========================================================
    # 차액 표시
    # =========================================================

    @classmethod
    def format_difference(
        cls,
        difference: int | float | None,
        unsold: bool = False,
    ) -> str:
        """
        차액을 화면 표시용으로 변환한다.

        구매:
            +2조 (현재 팔면)

        판매:
            +3조
        """

        if difference is None:
            return "-"

        try:
            difference = int(
                difference
            )

        except (
            TypeError,
            ValueError,
        ):
            return "-"

        if difference > 0:
            text = (
                "+"
                + cls.format_price(
                    difference
                )
            )

        elif difference < 0:
            text = (
                "-"
                + cls.format_price(
                    abs(
                        difference
                    )
                )
            )

        else:
            text = "0"

        if unsold:
            text += " (현재 팔면)"

        return text

    # =========================================================
    # 날짜 표시
    # =========================================================

    @staticmethod
    def format_date(
        trade_date: str | None,
    ) -> str:
        """거래일시를 화면 표시용으로 변환한다."""

        if not trade_date:
            return "-"

        try:
            dt = datetime.fromisoformat(
                trade_date.replace(
                    "Z",
                    "+00:00",
                )
            )

            return dt.strftime(
                "%Y-%m-%d %H:%M"
            )

        except (
            ValueError,
            TypeError,
        ):
            return str(
                trade_date
            )

    # =========================================================
    # 통계
    # =========================================================

    def calculate_statistics(
        self,
        trades: list[
            dict[str, Any]
        ],
    ) -> dict[str, Any]:
        """거래 내역 통계를 계산한다."""

        buy_trades = [
            trade
            for trade in trades
            if trade.get(
                "trade_type"
            ) == "구매"
        ]

        sell_trades = [
            trade
            for trade in trades
            if trade.get(
                "trade_type"
            ) == "판매"
        ]

        buy_amount = sum(
            int(
                trade.get(
                    "buy_price"
                )
                or 0
            )
            for trade in buy_trades
        )

        sell_amount = sum(
            int(
                trade.get(
                    "sell_price"
                )
                or 0
            )
            for trade in sell_trades
        )

        return {
            "total_count": len(
                trades
            ),

            "buy_count": len(
                buy_trades
            ),

            "sell_count": len(
                sell_trades
            ),

            "buy_amount": buy_amount,

            "sell_amount": sell_amount,

            "difference": (
                sell_amount
                - buy_amount
            ),
        }
from typing import Any

import httpx

from app.core.config import settings


class NexonAPIError(Exception):
    """NEXON Open API 요청 오류."""


class NexonClient:
    """NEXON Open API 클라이언트."""

    def __init__(self, api_key: str) -> None:
        api_key = api_key.strip()

        if not api_key:
            raise ValueError(
                "NEXON API KEY가 비어 있습니다."
            )

        self.api_key = api_key

    @property
    def headers(self) -> dict[str, str]:
        return {
            "x-nxopen-api-key": self.api_key,
            "Accept": "application/json",
        }

    def request(
        self,
        method: str,
        endpoint: str,
        **kwargs: Any,
    ) -> Any:
        """NEXON Open API에 HTTP 요청을 보낸다."""

        url = (
            f"{settings.NEXON_API_BASE_URL}"
            f"/{endpoint.lstrip('/')}"
        )

        headers = kwargs.pop("headers", {})

        request_headers = {
            **self.headers,
            **headers,
        }

        try:
            response = httpx.request(
                method=method,
                url=url,
                headers=request_headers,
                timeout=settings.REQUEST_TIMEOUT,
                **kwargs,
            )

        except httpx.TimeoutException as error:
            raise NexonAPIError(
                "NEXON API 요청 시간이 초과되었습니다."
            ) from error

        except httpx.RequestError as error:
            raise NexonAPIError(
                "NEXON API 서버에 연결할 수 없습니다.\n"
                f"{error}"
            ) from error

        # 정상 응답
        if 200 <= response.status_code < 300:
            if not response.content:
                return None

            try:
                return response.json()

            except ValueError as error:
                raise NexonAPIError(
                    "NEXON API 응답을 JSON으로 읽을 수 없습니다.\n"
                    f"응답: {response.text}"
                ) from error

        # 서버 응답 원문 확보
        try:
            error_body = response.json()

        except ValueError:
            error_body = response.text.strip()

        # HTTP 상태별 메시지
        if response.status_code == 400:
            raise NexonAPIError(
                "NEXON API 요청이 잘못되었습니다.\n\n"
                f"HTTP 상태 코드: 400\n"
                f"서버 응답: {error_body}"
            )

        if response.status_code == 401:
            raise NexonAPIError(
                "NEXON API KEY가 올바르지 않습니다.\n\n"
                f"서버 응답: {error_body}"
            )

        if response.status_code == 403:
            raise NexonAPIError(
                "NEXON API KEY 사용 권한이 없습니다.\n\n"
                f"서버 응답: {error_body}"
            )

        if response.status_code == 404:
            raise NexonAPIError(
                "요청한 FC Online 정보를 찾을 수 없습니다.\n\n"
                f"서버 응답: {error_body}"
            )

        if response.status_code == 429:
            raise NexonAPIError(
                "NEXON API 요청 횟수 제한에 도달했습니다.\n\n"
                f"서버 응답: {error_body}"
            )

        raise NexonAPIError(
            "NEXON API 요청에 실패했습니다.\n\n"
            f"HTTP 상태 코드: {response.status_code}\n"
            f"서버 응답: {error_body}"
        )

    def get_ouid(
        self,
        nickname: str,
    ) -> str:
        """FC Online 닉네임으로 OUID를 조회한다."""

        nickname = nickname.strip()

        if not nickname:
            raise ValueError(
                "FC Online 닉네임을 입력해주세요."
            )

        result = self.request(
            "GET",
            "/id",
            params={
                "nickname": nickname,
            },
        )

        if not isinstance(result, dict):
            raise NexonAPIError(
                "OUID 조회 응답 형식이 올바르지 않습니다."
            )

        ouid = result.get("ouid")

        if not ouid:
            raise NexonAPIError(
                "해당 닉네임의 OUID를 찾을 수 없습니다."
            )

        return ouid

    def get_user_info(
        self,
        ouid: str,
    ) -> dict[str, Any]:
        """OUID로 FC Online 기본 유저 정보를 조회한다."""

        ouid = ouid.strip()

        if not ouid:
            raise ValueError(
                "OUID가 비어 있습니다."
            )

        result = self.request(
            "GET",
            "/user/basic",
            params={
                "ouid": ouid,
            },
        )

        if not isinstance(result, dict):
            raise NexonAPIError(
                "유저 정보 응답 형식이 올바르지 않습니다."
            )

        return result

    def get_trade_history(
        self,
        trade_type: str,
        offset: int = 0,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """API KEY에 연결된 FC Online 계정의 거래 기록을 조회한다."""

        trade_type = trade_type.strip().lower()

        if trade_type not in {"buy", "sell"}:
            raise ValueError(
                "거래 유형은 buy 또는 sell이어야 합니다."
            )

        if offset < 0:
            raise ValueError(
                "offset은 0 이상이어야 합니다."
            )

        if limit < 1 or limit > 100:
            raise ValueError(
                "limit은 1 이상 100 이하이어야 합니다."
            )

        result = self.request(
            "GET",
            "/user/trade",
            params={
                "tradetype": trade_type,
                "offset": offset,
                "limit": limit,
            },
        )

        if not isinstance(result, list):
            raise NexonAPIError(
                "거래 기록 응답 형식이 올바르지 않습니다."
            )

        return result

    def get_player_metadata(
        self,
    ) -> list[dict[str, Any]]:
        """FC Online 선수 메타데이터를 조회한다."""

        url = (
            "https://open.api.nexon.com"
            "/static/fconline/meta/spid.json"
        )

        try:
            response = httpx.get(
                url,
                headers=self.headers,
                timeout=settings.REQUEST_TIMEOUT,
            )

        except httpx.TimeoutException as error:
            raise NexonAPIError(
                "선수 메타데이터 요청 시간이 초과되었습니다."
            ) from error

        except httpx.RequestError as error:
            raise NexonAPIError(
                "선수 메타데이터 서버에 연결할 수 없습니다.\n"
                f"{error}"
            ) from error

        if not 200 <= response.status_code < 300:
            try:
                error_body = response.json()

            except ValueError:
                error_body = response.text.strip()

            raise NexonAPIError(
                "선수 메타데이터 요청에 실패했습니다.\n\n"
                f"HTTP 상태 코드: {response.status_code}\n"
                f"서버 응답: {error_body}"
            )

        try:
            result = response.json()

        except ValueError as error:
            raise NexonAPIError(
                "선수 메타데이터를 JSON으로 읽을 수 없습니다."
            ) from error

        if not isinstance(result, list):
            raise NexonAPIError(
                "선수 메타데이터 응답 형식이 올바르지 않습니다."
            )

        return result

    def get_season_metadata(
        self,
    ) -> list[dict[str, Any]]:
        """FC Online 시즌 메타데이터를 조회한다."""

        url = (
            "https://open.api.nexon.com"
            "/static/fconline/meta/seasonid.json"
        )

        try:
            response = httpx.get(
                url,
                headers=self.headers,
                timeout=settings.REQUEST_TIMEOUT,
            )

        except httpx.TimeoutException as error:
            raise NexonAPIError(
                "시즌 메타데이터 요청 시간이 초과되었습니다."
            ) from error

        except httpx.RequestError as error:
            raise NexonAPIError(
                "시즌 메타데이터 서버에 연결할 수 없습니다.\n"
                f"{error}"
            ) from error

        if not 200 <= response.status_code < 300:
            try:
                error_body = response.json()

            except ValueError:
                error_body = response.text.strip()

            raise NexonAPIError(
                "시즌 메타데이터 요청에 실패했습니다.\n\n"
                f"HTTP 상태 코드: {response.status_code}\n"
                f"서버 응답: {error_body}"
            )

        try:
            result = response.json()

        except ValueError as error:
            raise NexonAPIError(
                "시즌 메타데이터를 JSON으로 읽을 수 없습니다."
            ) from error

        if not isinstance(result, list):
            raise NexonAPIError(
                "시즌 메타데이터 응답 형식이 올바르지 않습니다."
            )

        return result
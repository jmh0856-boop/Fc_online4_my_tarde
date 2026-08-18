import httpx

from app.core.config import settings


class NexonAPIError(Exception):
    """NEXON Open API 호출 중 발생한 오류"""


class NexonClient:
    BASE_URL = "https://open.api.nexon.com"

    def __init__(self):
        self.headers = {
            "x-nxopen-api-key": settings.nexon_api_key,
        }

    async def _get(
        self,
        path: str,
        params: dict | None = None,
    ):
        async with httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=10.0,
        ) as client:
            response = await client.get(
                path,
                params=params,
            )

        if response.status_code != 200:
            try:
                error_data = response.json()
            except Exception:
                error_data = response.text

            raise NexonAPIError(
                f"NEXON API 오류 ({response.status_code}): {error_data}"
            )

        return response.json()

    async def get_ouid(self, nickname: str) -> str:
        data = await self._get(
            "/fconline/v1/id",
            params={
                "nickname": nickname,
            },
        )

        return data["ouid"]

    async def get_trade_history(
        self,
        ouid: str,
        trade_type: str,
    ):
        return await self._get(
            "/fconline/v1/user/trade",
            params={
                "ouid": ouid,
                "tradetype": trade_type,
            },
        )

    async def get_spid_metadata(self):
        return await self._get(
            "/static/fconline/meta/spid.json"
        )

    async def get_season_metadata(self):
        return await self._get(
            "/static/fconline/meta/seasonid.json"
        )
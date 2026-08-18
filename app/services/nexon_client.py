import httpx

from app.core.config import settings


class NexonAPIError(Exception):
    pass


class NexonClient:

    def __init__(self):
        self.base_url = settings.nexon_base_url

        self.headers = {
            "x-nxopen-api-key": settings.nexon_api_key,
        }

    async def get_ouid(self, nickname: str) -> str:
        url = f"{self.base_url}/fconline/v1/id"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params={
                    "nickname": nickname,
                },
            )

        if response.status_code != 200:
            raise NexonAPIError(
                f"NEXON API 오류: "
                f"status={response.status_code}, "
                f"body={response.text}"
            )

        data = response.json()

        if "ouid" not in data:
            raise NexonAPIError(
                f"응답에 ouid가 없습니다: {data}"
            )

        return data["ouid"]

    async def get_trade_history(self, ouid: str, tradetype: str):
        url = f"{self.base_url}/fconline/v1/user/trade"

        async with httpx.AsyncClient() as client:
            response = await client.get(
                url,
                headers=self.headers,
                params={
                    "ouid": ouid,
                    "tradetype": tradetype,
                    "offset": 0,
                    "limit": 10,
                },
            )

        if response.status_code != 200:
            raise NexonAPIError(
                f"NEXON API 오류: "
                f"status={response.status_code}, "
                f"body={response.text}"
            )

        return response.json()


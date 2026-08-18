from app.services.nexon_client import NexonClient


class UserService:

    def __init__(self, nexon_client: NexonClient):
        self.nexon_client = nexon_client

    async def find_ouid(self, nickname: str) -> str:
        return await self.nexon_client.get_ouid(nickname)

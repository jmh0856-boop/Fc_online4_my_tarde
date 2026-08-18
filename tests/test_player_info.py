import asyncio

from app.services.nexon_client import NexonClient
from app.services.player_service import PlayerService


async def main():
    client = NexonClient()
    service = PlayerService(client)

    spid = 851265650

    info = await service.get_player_info(spid)

    print("SPID:", spid)
    print("선수 정보:")
    print(info)


if __name__ == "__main__":
    asyncio.run(main())
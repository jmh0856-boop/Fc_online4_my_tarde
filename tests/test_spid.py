import asyncio

from app.services.nexon_client import NexonClient
from app.services.player_service import PlayerService


async def main():
    client = NexonClient()
    player_service = PlayerService(client)

    # 전체 SPID 데이터 확인
    data = await client.get_spid_metadata()

    print("자료형:", type(data))
    print("데이터 개수:", len(data))
    print("첫 번째 데이터:", data[0])

    # ID -> 선수 이름
    spid = 100000041
    name = await player_service.get_player_name(spid)

    print()
    print("SPID:", spid)
    print("선수 이름:", name)

    # 선수 이름 -> ID
    player_ids = await player_service.get_player_ids("이니에스타")

    print()
    print("선수 이름: 이니에스타")
    print("SPID 개수:", len(player_ids))
    print("SPID 목록:", player_ids[:10])

if __name__ == "__main__":
    asyncio.run(main())
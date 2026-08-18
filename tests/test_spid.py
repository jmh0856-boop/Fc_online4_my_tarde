import asyncio

from app.services.nexon_client import NexonClient


async def main():
    client = NexonClient()

    data = await client.get_spid_metadata()

    print("자료형:", type(data))
    print("데이터 개수:", len(data))
    print("첫 번째 데이터:")
    print(data[0])


if __name__ == "__main__":
    asyncio.run(main())
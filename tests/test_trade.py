import asyncio

from app.services.nexon_client import NexonClient
from app.services.player_service import PlayerService
from app.services.trade_service import TradeService


async def main():
    client = NexonClient()
    player_service = PlayerService(client)
    trade_service = TradeService(
        nexon_client=client,
        player_service=player_service,
    )

    nickname = "이집골맛집"

    # 닉네임 → OUID
    ouid = await client.get_ouid(nickname)

    print("닉네임:", nickname)
    print("OUID:", ouid)

    # 거래내역 조회 + 선수 이름 변환
    trades = await trade_service.get_trades(
        ouid=ouid,
        trade_type="buy",
    )

    print()
    print("거래 데이터 개수:", len(trades))

    if trades:
        print()
        print("가공된 첫 번째 거래 데이터:")
        print(trades[0])


if __name__ == "__main__":
    asyncio.run(main())
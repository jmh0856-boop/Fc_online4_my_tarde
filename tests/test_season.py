import asyncio

from app.services.nexon_client import NexonClient


async def main():
    client = NexonClient()

    spids = await client.get_spid_metadata()
    seasons = await client.get_season_metadata()

    target_spid = 851265650

    player = next(
        player
        for player in spids
        if player["id"] == target_spid
    )

    season_id = target_spid // 1_000_000

    season = next(
        (
            season
            for season in seasons
            if season["seasonId"] == season_id
        ),
        None,
    )

    print("SPID:", target_spid)
    print("선수 이름:", player["name"])
    print("추출한 시즌 ID:", season_id)
    print("시즌 정보:", season)


if __name__ == "__main__":
    asyncio.run(main())
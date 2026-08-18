from app.services.nexon_client import NexonClient


class PlayerService:

    def __init__(self, nexon_client: NexonClient):
        self.nexon_client = nexon_client

        self._players_by_id: dict[int, str] | None = None
        self._players_by_name: dict[str, list[int]] | None = None
        self._seasons_by_id: dict[int, dict] | None = None

    async def _load_players(self):
        if self._players_by_id is not None:
            return

        players = await self.nexon_client.get_spid_metadata()

        self._players_by_id = {}
        self._players_by_name = {}

        for player in players:
            spid = player["id"]
            name = player["name"]

            self._players_by_id[spid] = name

            self._players_by_name.setdefault(name, []).append(spid)

    async def _load_seasons(self):
        if self._seasons_by_id is not None:
            return

        seasons = await self.nexon_client.get_season_metadata()

        self._seasons_by_id = {
            season["seasonId"]: season
            for season in seasons
        }

    async def get_player_name(self, spid: int) -> str | None:
        await self._load_players()

        return self._players_by_id.get(spid)

    async def get_player_ids(self, name: str) -> list[int]:
        await self._load_players()

        return self._players_by_name.get(name, [])

    async def get_season(self, spid: int) -> dict | None:
        await self._load_seasons()

        season_id = spid // 1_000_000

        return self._seasons_by_id.get(season_id)

    def get_player_image_url(self, spid: int) -> str:
        return (
            "https://fco.dn.nexoncdn.co.kr/"
            f"live/externalAssets/common/playersAction/p{spid}.png"
        )

    async def get_player_info(self, spid: int) -> dict | None:
        await self._load_players()
        await self._load_seasons()

        player_name = self._players_by_id.get(spid)

        if player_name is None:
            return None

        season_id = spid // 1_000_000
        season = self._seasons_by_id.get(season_id)

        return {
            "spid": spid,
            "player_name": player_name,
            "season_id": season_id,
            "season_name": (
                season["className"]
                if season
                else None
            ),
            "season_img": (
                season["seasonImg"]
                if season
                else None
            ),
            "player_img": self.get_player_image_url(spid),
        }
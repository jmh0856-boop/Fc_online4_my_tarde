from datetime import datetime

from pydantic import BaseModel


class Trade(BaseModel):
    trade_type: str
    trade_date: datetime
    sale_sn: str
    spid: int
    player_name: str | None = None
    season_id: int | None = None
    season_name: str | None = None
    season_img: str | None = None
    player_img: str | None = None
    grade: int
    value: int


class TradeList(BaseModel):
    items: list[Trade]
    page: int
    size: int
    total: int
    has_next: bool
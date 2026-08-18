from enum import Enum

from fastapi import APIRouter, Depends, Query

from app.schemas.trade import Trade
from app.services.nexon_client import NexonClient
from app.services.player_service import PlayerService
from app.services.trade_service import TradeService


class TradeType(str, Enum):
    BUY = "buy"
    SELL = "sell"
    ALL = "all"


router = APIRouter(
    prefix="/trades",
    tags=["trades"],
)


def get_trade_service() -> TradeService:
    nexon_client = NexonClient()
    player_service = PlayerService(nexon_client)

    return TradeService(
        nexon_client=nexon_client,
        player_service=player_service,
    )


@router.get("/{ouid}", response_model=dict)
async def get_trades(
    ouid: str,

    tradetype: TradeType = Query(
        default=TradeType.BUY,
        description="거래 유형: buy, sell, all",
    ),

    start_date: str | None = Query(
        default=None,
        description="조회 시작일 (YYYY-MM-DD)",
    ),

    end_date: str | None = Query(
        default=None,
        description="조회 종료일 (YYYY-MM-DD)",
    ),

    page: int = Query(
        default=1,
        ge=1,
    ),

    size: int = Query(
        default=10,
        ge=1,
        le=100,
    ),

    service: TradeService = Depends(get_trade_service),
):
    return await service.get_trades(
        ouid,
        tradetype.value,
        page,
        size,
        start_date,
        end_date,
    )
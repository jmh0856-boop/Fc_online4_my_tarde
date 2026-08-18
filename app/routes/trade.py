from fastapi import APIRouter, Depends, Query

from app.services.nexon_client import NexonClient
from app.services.trade_service import TradeService


router = APIRouter(
    prefix="/trades",
    tags=["trades"],
)


def get_trade_service() -> TradeService:
    return TradeService(
        nexon_client=NexonClient()
    )


@router.get("/{ouid}")
async def get_trades(
    ouid: str,
    tradetype: str = Query(
        default="buy",
        description="거래 유형: buy 또는 sell",
    ),
    service: TradeService = Depends(get_trade_service),
):
    return await service.get_trades(
        ouid,
        tradetype,
    )

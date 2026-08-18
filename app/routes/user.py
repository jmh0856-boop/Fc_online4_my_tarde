from fastapi import APIRouter, Depends, HTTPException

from app.schemas.user import UserResponse
from app.services.nexon_client import NexonAPIError, NexonClient
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


def get_user_service() -> UserService:
    return UserService(
        nexon_client=NexonClient()
    )


@router.get("/{nickname}", response_model=UserResponse)
async def get_user(
    nickname: str,
    service: UserService = Depends(get_user_service),
):
    try:
        ouid = await service.find_ouid(nickname)

        return UserResponse(
            nickname=nickname,
            ouid=ouid,
        )

    except NexonAPIError as e:
        raise HTTPException(
            status_code=502,
            detail=str(e),
        )
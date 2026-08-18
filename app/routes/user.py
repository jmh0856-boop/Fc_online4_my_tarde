from fastapi import APIRouter, Header, HTTPException

from app.schemas.user import UserResponse
from app.services.nexon_client import NexonAPIError, NexonClient
from app.services.user_service import UserService


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/{nickname}", response_model=UserResponse)
async def get_user(
    nickname: str,
    x_nexon_api_key: str = Header(...),
):
    try:
        nexon_client = NexonClient(
            api_key=x_nexon_api_key
        )

        service = UserService(
            nexon_client=nexon_client
        )

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
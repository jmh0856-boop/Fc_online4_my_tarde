from typing import Any

from app.services.nexon_client import NexonClient


class UserService:
    """FC Online 유저 관련 기능을 담당한다."""

    def __init__(self, nexon_client: NexonClient) -> None:
        self.nexon_client = nexon_client

    def get_user_by_nickname(
        self,
        nickname: str,
    ) -> dict[str, Any]:
        """
        닉네임으로 FC Online 유저 정보를 조회한다.

        반환값:
            {
                "nickname": str,
                "ouid": str,
                "level": int | None,
                "user_info": dict
            }
        """

        nickname = nickname.strip()

        if not nickname:
            raise ValueError(
                "FC Online 닉네임을 입력해주세요."
            )

        # 닉네임 → OUID
        ouid = self.nexon_client.get_ouid(
            nickname
        )

        # OUID → 기본 유저 정보
        user_info = self.nexon_client.get_user_info(
            ouid
        )

        return {
            "nickname": nickname,
            "ouid": ouid,
            "level": user_info.get("level"),
            "user_info": user_info,
        }

    def get_user_level(
        self,
        nickname: str,
    ) -> int | None:
        """닉네임으로 유저 레벨을 조회한다."""

        user = self.get_user_by_nickname(
            nickname
        )

        return user.get("level")
from pydantic import BaseModel


class UserResponse(BaseModel):
    nickname: str
    ouid: str
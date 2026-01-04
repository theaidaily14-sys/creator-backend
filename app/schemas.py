from pydantic import BaseModel, EmailStr, constr
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    password: constr(min_length=8, max_length=72)

class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True

class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ChannelOut(BaseModel):
    id: int
    platform: str
    platform_channel_id: str
    channel_title: str
    channel_url: str

    class Config:
        from_attributes = True

class ChannelsListOut(BaseModel):
    channels: List[ChannelOut]

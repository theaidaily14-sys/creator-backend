from pydantic import BaseModel, EmailStr
from typing import List

class UserCreate(BaseModel):
    email: EmailStr
    password: str

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

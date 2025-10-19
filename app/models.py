from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column
from datetime import date, datetime, timedelta
from sqlalchemy.dialects.mysql import LONGTEXT

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    nickname: str
    email: str
    password_hash: str
    birthday: Optional[date] = None
    bio: Optional[str] = None
    phone: Optional[str] = None
    is_2fa_enabled: bool = False
    otp_secret: Optional[str] = None  
    avatar: Optional[str] = Field(
        default=None,
        sa_column=Column(LONGTEXT)
    )

class UserSession(SQLModel, table=True):
    token: str = Field(primary_key=True, index=True)
    user_id: int = Field(foreign_key="user.id", nullable=False)
    created: datetime = Field(default_factory=datetime.utcnow)
    expires: datetime = Field(default_factory=lambda: datetime.utcnow() + timedelta(days=7))
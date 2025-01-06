from sqlalchemy import (
    BigInteger,
    String,
    Integer,
    LargeBinary,
    DateTime,
    func,
    ForeignKey,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.dialects.postgresql import JSON

from datetime import datetime
from bot.session import engine


class Base(AsyncAttrs, DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(BigInteger, unique=True)


class User_Data(Base):
    __tablename__ = "userdata"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(ForeignKey("users.vk_id"))
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    surname: Mapped[str] = mapped_column(String(100), nullable=False)
    age: Mapped[int] = mapped_column(nullable=False)
    city: Mapped[str] = mapped_column(String(100), nullable=False)
    profile_url: Mapped[str] = mapped_column(String(100), nullable=False, unique=True)
    photo_1: Mapped[str] = mapped_column(String(100))
    photo_2: Mapped[bytes] = mapped_column(String(100))
    photo_3: Mapped[bytes] = mapped_column(String(100))

class Blacklist(Base):
    __tablename__ = "blacklist"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(ForeignKey("users.vk_id"))
    blocked_users_id: Mapped[list] = mapped_column(JSON)


class Favourite(Base):
    __tablename__ = "favourite"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(ForeignKey("users.vk_id"))
    favourite_users_id: Mapped[list] = mapped_column(JSON)

class SearchUsers(Base):
    __tablename__ = "searchusers"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(ForeignKey("users.vk_id"))
    search_user_id: Mapped[int] = mapped_column(BigInteger)

class UserParams(Base):
    __tablename__ = "userparams"

    id: Mapped[int] = mapped_column(primary_key=True)
    vk_id: Mapped[int] = mapped_column(ForeignKey("users.vk_id"))
    sex: Mapped[str] = mapped_column(String(10))
    
async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        return "Tables deleted"


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

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
from database.session import engine


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
    photo_1: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    photo_2: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    photo_3: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)

    def to_dict(self):
        return {
            "id": self.id,
            "vk_id": self.vk_id,
            "name": self.name,
            "surname": self.surname,
            "age": self.age,
            "profile_url": self.profile_url,
            "photo_1": self.photo_1,
            "photo_2": self.photo_2,
            "photo_3": self.photo_3,
        }


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


async def delete_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        return "Tables deleted"


async def async_main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, BigInteger, Boolean, func
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())  # Добавлен столбец created_at


class Search_Result(Base):
    __tablename__ = "search_result"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.user_id"))
    result_user_id: Mapped[int] = mapped_column(BigInteger)
    favorites: Mapped[bool] = mapped_column(Boolean, default=False)
    blacklist: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[DateTime] = mapped_column(DateTime, default=func.now())  # Добавлен столбец created_at
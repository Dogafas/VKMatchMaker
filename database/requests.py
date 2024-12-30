from database.session import async_session
from database.models import User, User_Data, Blacklist, Favourite
from sqlalchemy import select, update, delete, or_
from sqlalchemy.future import select


# Создание юзера
async def set_user(**kwargs):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.vk_id == kwargs["vk_id"]))

        if not user:
            session.add(User(vk_id=kwargs["vk_id"]))
            session.add(
                User_Data(
                    vk_id=kwargs["vk_id"],
                    name=kwargs["name"],
                    surname=kwargs["surname"],
                    age=kwargs["age"],
                    city=kwargs["city"],
                    profile_url=kwargs["profile_url"],
                    photo_1=kwargs["photo_1"],
                    photo_2=kwargs["photo_2"],
                    photo_3=kwargs["photo_3"],
                )
            )
            await session.commit()
            session.add(Blacklist(vk_id=kwargs["vk_id"], blocked_users_id=[]))
            session.add(Favourite(vk_id=kwargs["vk_id"], favourite_users_id=[]))
            await session.commit()
            return "User created"

        return "User already exists"


# Получение данных юзера
async def get_user(vk_id):
    async with async_session() as session:
        user = await session.scalar(select(User_Data).where(User_Data.vk_id == vk_id))
        return (
            {
                column.name: getattr(user, column.name)
                for column in user.__table__.columns
            }
            if user
            else None
        )


# Удаление юзера
async def delete_user(vk_id):
    async with async_session() as session:
        await session.execute(delete(User_Data).where(User_Data.vk_id == vk_id))
        await session.execute(delete(Blacklist).where(Blacklist.vk_id == vk_id))
        await session.execute(delete(Favourite).where(Favourite.vk_id == vk_id))
        await session.execute(delete(User).where(User.vk_id == vk_id))
        await session.commit()


# Добавление в черный список
async def add_user_to_blacklist(vk_id, blocked_user_id):
    async with async_session() as session:
        user_blacklist = await session.scalar(
            select(Blacklist).where(Blacklist.vk_id == vk_id)
        )

        if blocked_user_id in user_blacklist.blocked_users_id:
            return "User already in blacklist"

        user_blacklist.blocked_users_id.append(blocked_user_id)

        update_blacklist = (
            update(Blacklist)
            .where(Blacklist.vk_id == vk_id)
            .values(blocked_users_id=user_blacklist.blocked_users_id)
        )
        await session.execute(update_blacklist)
        await session.commit()
        return "User added to blacklist"


# Удаление из черного списка
async def remove_user_from_blacklist(vk_id, blocked_user_id):
    async with async_session() as session:
        user_blacklist = await session.scalar(
            select(Blacklist).where(Blacklist.vk_id == vk_id)
        )

        if blocked_user_id not in user_blacklist.blocked_users_id:
            return "User not in blacklist"

        user_blacklist.blocked_users_id.remove(blocked_user_id)

        update_blacklist = (
            update(Blacklist)
            .where(Blacklist.vk_id == vk_id)
            .values(blocked_users_id=user_blacklist.blocked_users_id)
        )
        await session.execute(update_blacklist)
        await session.commit()
        return "User removed from blacklist"


# Получение черного списка юзера
async def get_user_blacklist(vk_id):
    async with async_session() as session:
        user_blacklist = await session.scalar(
            select(Blacklist).where(Blacklist.vk_id == vk_id)
        )
        return user_blacklist.blocked_users_id if user_blacklist else None


# Добавление в избранное
async def add_user_to_favourites(vk_id, favourite_user_id):
    async with async_session() as session:
        user_favourites = await session.scalar(
            select(Favourite).where(Favourite.vk_id == vk_id)
        )

        if favourite_user_id in user_favourites.favourite_users_id:
            return "User already in favourites"

        user_favourites.favourite_users_id.append(favourite_user_id)

        update_favourites = (
            update(Favourite)
            .where(Favourite.vk_id == vk_id)
            .values(favourite_users_id=user_favourites.favourite_users_id)
        )
        await session.execute(update_favourites)
        await session.commit()
        return "User added to favourites"


# Удаление из избранного
async def remove_user_from_favourites(vk_id, favourite_user_id):
    async with async_session() as session:
        user_favourites = await session.scalar(
            select(Favourite).where(Favourite.vk_id == vk_id)
        )

        if favourite_user_id not in user_favourites.favourite_users_id:
            return "User not in favourites"

        user_favourites.favourite_users_id.remove(favourite_user_id)

        update_favourites = (
            update(Favourite)
            .where(Favourite.vk_id == vk_id)
            .values(favourite_users_id=user_favourites.favourite_users_id)
        )
        await session.execute(update_favourites)
        await session.commit()
        return "User removed from favourites"


# Получение избранных пользователей юзера
async def get_user_favourites(vk_id):
    async with async_session() as session:
        user_favourites = await session.scalar(
            select(Favourite).where(Favourite.vk_id == vk_id)
        )
        return user_favourites.favourite_users_id if user_favourites else None

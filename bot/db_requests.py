from session import session
from models import User, User_Search_Params, Search_Result
from sqlalchemy import select, update, delete, or_
from sqlalchemy.future import select


def set_user(user_id):
    user = session.scalar(select(User).where(User.user_id == user_id))

    if not user:
        session.add(User(user_id=user_id, current_index=0))
        session.commit()
        return "User created"

    return "User already exists"


def save_user_search_params(user_id, sex, age, city_id):
    user = session.scalar(
        select(User_Search_Params).where(User_Search_Params.user_id == user_id)
    )

    if not user:
        session.add(
            User_Search_Params(user_id=user_id, sex=sex, age=age, city_id=city_id)
        )
        session.commit()
        return "Search params saved"

    for key, value in {"sex": sex, "age": age, "city_id": city_id}.items():
        setattr(user, key, value)

    session.commit()
    return "Search params updated"


def get_user_search_params(user_id):
    user_search_params = session.scalar(
        select(User_Search_Params).where(User_Search_Params.user_id == user_id)
    )

    if not user_search_params:
        return None

    return {
        "sex": user_search_params.sex,
        "age": user_search_params.age,
        "city_id": user_search_params.city_id,
    }


def save_search_results(user_id, result_user_id, search_params_id):
    if_search_user = session.scalar(
        select(Search_Result).where(
            Search_Result.user_id == user_id,
            Search_Result.result_user_id == result_user_id,
        )
    )
    if not if_search_user:
        session.add(
            Search_Result(
                user_id=user_id,
                result_user_id=result_user_id,
                search_params_id=search_params_id,
            )
        )
        session.commit()
        return "Search results saved"
    return "User already exist"


def get_search_results(user_id):
    search_results = session.scalar(
        select(Search_Result).where(Search_Result.user_id == user_id)
    )
    if not search_results:
        return None

    return {
        "result_user_id": search_results.result_user_id,
        "search_params_id": search_results.search_params_id,
    }


def get_user_index(user_id):
    index = session.scalar(select(User).where(User.user_id == user_id))

    return index.current_index


def change_user_index(user_id, index):
    change_index = session.scalar(select(User).where(User.user_id == user_id))

    change_index.current_index = index
    session.commit()

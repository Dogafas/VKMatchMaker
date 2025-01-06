# db_requests.py
from session import session
from models import User, Search_Result
from sqlalchemy import select, update, delete, or_
from sqlalchemy.future import select
import logging

# настройка логгирования
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def set_user(user_id):
    logging.info(f"Начало set_user с user_id: {user_id}")
    user = session.scalar(select(User).where(User.user_id == user_id))

    if not user:
        session.add(User(user_id=user_id))
        session.commit()
        logging.info(f"Создан новый пользователь с user_id: {user_id}")
        return "User created"

    logging.info(f"Пользователь с user_id: {user_id} уже существует")
    return "User already exists"


def save_search_results(user_id, result_user_id):
    logging.info(f"Начало save_search_results с user_id: {user_id}, result_user_id: {result_user_id}")
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
            )
        )
        session.commit()
        logging.info(f"Результаты поиска сохранены для user_id: {user_id}, result_user_id: {result_user_id}")
        return "Search results saved"
    logging.info(f"Результаты поиска для user_id: {user_id}, result_user_id: {result_user_id} уже существуют")
    return "User already exist"


def get_search_results(user_id):
    logging.info(f"Начало get_search_results с user_id: {user_id}")
    search_results = session.scalars(
        select(Search_Result).where(Search_Result.user_id == user_id)
    ).all()

    if not search_results:
        logging.info(f"Результаты поиска для user_id: {user_id} не найдены")
        return []

    logging.info(f"Результаты поиска для user_id: {user_id} получены: {search_results}")
    return search_results


def get_user_index(user_id):
    logging.info(f"Начало get_user_index с user_id: {user_id}")
    index = session.scalar(select(User).where(User.user_id == user_id))
    return index



def set_favorite(search_result_id):
    """
    Устанавливает флаг favorites в True для указанного результата поиска.
    """
    logging.info(f"Начало set_favorite с search_result_id: {search_result_id}")

    # Обновляем запись в таблице Search_Result
    stmt = (
        update(Search_Result)
        .where(
            (Search_Result.id == search_result_id)
        )
        .values(favorites=True)
    )
    logging.info(f"SQL запрос: {stmt}")
    session.execute(stmt)
    session.commit()

    logging.info(f"Флаг favorites установлен в True для search_result_id: {search_result_id}")
    return "Favorite flag set to True"


def set_blacklist(search_result_id):
    """
    Устанавливает флаг blacklist в True для указанного результата поиска.
    """
    logging.info(f"Начало set_blacklist с search_result_id: {search_result_id}")
    # Обновляем запись в таблице Search_Result
    stmt = (
        update(Search_Result)
        .where(
            (Search_Result.id == search_result_id)
        )
        .values(blacklist=True)
    )
    logging.info(f"SQL запрос: {stmt}")
    session.execute(stmt)
    session.commit()

    logging.info(f"Флаг blacklist установлен в True для search_result_id: {search_result_id}")
    return "Blacklist flag set to True"
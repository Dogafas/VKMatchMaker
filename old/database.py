import os
import logging
import psycopg2
from dotenv import load_dotenv

load_dotenv()

# Получаем данные для подключения к базе данных из переменных окружения
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST")
POSTGRES_PORT = os.getenv("POSTGRES_PORT")
POSTGRES_DB = os.getenv("POSTGRES_DB")


# Функция для подключения к базе данных
def get_db_connection():
    try:
        conn = psycopg2.connect(
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB
        )
        logging.info("Успешное подключение к базе данных")
        return conn
    except psycopg2.Error as e:
        logging.error(f"Ошибка подключения к базе данных: {e}")
        return None

def save_user_search_params(user_id, sex, age, city_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO user_search_params (user_id, sex, age, city_id)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (user_id) DO UPDATE
                    SET sex = %s, age = %s, city_id = %s;
                    """,
                    (user_id, sex, age, city_id, sex, age, city_id)
                )
                conn.commit()
                logging.info(f"Параметры поиска пользователя {user_id} сохранены в БД")
        except psycopg2.Error as e:
            logging.error(f"Ошибка сохранения параметров поиска в БД: {e}")
        finally:
            conn.close()

def get_user_search_params(user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT sex, age, city_id FROM user_search_params WHERE user_id = %s",
                    (user_id,)
                )
                params = cur.fetchone()
                if params:
                    logging.info(f"Параметры поиска пользователя {user_id} получены из БД")
                    return {"sex": params[0], "age": params[1], "city_id": params[2]}
                else:
                   logging.info(f"Параметры поиска пользователя {user_id} в БД не найдены")
                   return None
        except psycopg2.Error as e:
            logging.error(f"Ошибка получения параметров поиска из БД: {e}")
            return None
        finally:
            conn.close()

def save_search_results(user_id, result_user_id, search_params_id):
        conn = get_db_connection()
        if conn:
           try:
               with conn.cursor() as cur:
                 cur.execute(
                    "INSERT INTO user_search_results (user_id, result_user_id, search_params_id) VALUES (%s, %s, %s)",
                    (user_id, result_user_id, search_params_id)
                 )
                 conn.commit()
                 logging.info(f"Результат поиска пользователя {user_id} сохранен в БД")
           except psycopg2.Error as e:
               logging.error(f"Ошибка сохранения результата поиска в БД: {e}")
           finally:
               conn.close()

def get_search_results(user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
               cur.execute(
                   "SELECT result_user_id FROM user_search_results WHERE user_id = %s",
                   (user_id,)
                )
               results = cur.fetchall()
               if results:
                   logging.info(f"Результаты поиска пользователя {user_id} получены из БД")
                   return [result[0] for result in results]
               else:
                   logging.info(f"Результаты поиска пользователя {user_id} в БД не найдены")
                   return []
        except psycopg2.Error as e:
            logging.error(f"Ошибка получения результатов поиска из БД: {e}")
            return []
        finally:
            conn.close()
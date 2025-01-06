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

def save_user(vk_user_id, first_name, last_name, city, search_offset = 0):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (vk_user_id, first_name, last_name, city, search_offset)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (vk_user_id) DO UPDATE
                    SET first_name = %s, last_name = %s, city = %s, search_offset = %s;
                    """,
                    (vk_user_id, first_name, last_name, city, search_offset, first_name, last_name, city, search_offset)
                )
                conn.commit()
                logging.info(f"Пользователь {vk_user_id} сохранен/обновлен в БД")
                # Получаем id пользователя
                cur.execute("SELECT id FROM users WHERE vk_user_id = %s", (vk_user_id,))
                user_id = cur.fetchone()[0]
                return user_id
        except psycopg2.Error as e:
            logging.error(f"Ошибка сохранения/обновления пользователя в БД: {e}")
            return None
        finally:
            conn.close()
    return None

def get_user_id(vk_user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT id, search_offset, last_viewed_result_id FROM users WHERE vk_user_id = %s", (vk_user_id,))
                user_data = cur.fetchone()
                if user_data:
                    logging.info(f"id пользователя {vk_user_id} получен из БД")
                    return {"id":user_data[0], "offset":user_data[1], "last_viewed_result_id":user_data[2]} 
                else:
                    logging.info(f"id пользователя {vk_user_id} в БД не найден")
                    return None
        except psycopg2.Error as e:
            logging.error(f"Ошибка при получении user_id: {e}")
            return None
        finally:
            conn.close()
    return None

def update_user_offset(vk_user_id, search_offset):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET search_offset = %s WHERE vk_user_id = %s",
                    (search_offset, vk_user_id)
                )
                conn.commit()
                logging.info(f"Смещение пользователя {vk_user_id} обновлено в БД")
        except psycopg2.Error as e:
            logging.error(f"Ошибка при обновлении смещения пользователя в БД: {e}")
        finally:
            conn.close()

def update_user_last_viewed_result_id(vk_user_id, last_viewed_result_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "UPDATE users SET last_viewed_result_id = %s WHERE vk_user_id = %s",
                    (last_viewed_result_id, vk_user_id)
                )
                conn.commit()
                logging.info(f"Индекс просмотра пользователя {vk_user_id} обновлен в БД")
        except psycopg2.Error as e:
            logging.error(f"Ошибка при обновлении индекса просмотра пользователя в БД: {e}")
        finally:
            conn.close()

def save_search_result(user_id, vk_search_user_id, first_name, last_name, profile_url):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO search_results (user_id, vk_search_user_id, first_name, last_name, profile_url)
                    VALUES (%s, %s, %s, %s, %s)
                    ON CONFLICT (user_id, vk_search_user_id) DO UPDATE
                    SET first_name = %s, last_name = %s, profile_url = %s;
                    """,
                    (user_id, vk_search_user_id, first_name, last_name, profile_url, first_name, last_name, profile_url)
                )
                conn.commit()
                logging.info(f"Результат поиска пользователя {vk_search_user_id} сохранен/обновлен в БД")
        except psycopg2.Error as e:
            logging.error(f"Ошибка сохранения/обновления результата поиска в БД: {e}")
        finally:
            conn.close()

def get_search_results(user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT vk_search_user_id FROM search_results WHERE user_id = %s",
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
    return []

def is_search_result_exists(user_id, vk_search_user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM search_results WHERE user_id = %s AND vk_search_user_id = %s",
                    (user_id, vk_search_user_id)
                )
                return cur.fetchone() is not None
        except psycopg2.Error as e:
            logging.error(f"Ошибка при проверке результата поиска в БД: {e}")
            return False
        finally:
             conn.close()
    return False

def save_blacklisted_user(user_id, vk_blacklisted_user_id, profile_url):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO blacklisted_users (user_id, vk_blacklisted_user_id, profile_url)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (user_id, vk_blacklisted_user_id) DO UPDATE
                    SET profile_url = %s;
                    """,
                   (user_id, vk_blacklisted_user_id, profile_url, profile_url)
                )
                conn.commit()
                logging.info(f"Пользователь {vk_blacklisted_user_id} добавлен в черный список")
        except psycopg2.Error as e:
            logging.error(f"Ошибка добавления пользователя в черный список: {e}")
        finally:
            conn.close()

def is_user_blacklisted(user_id, vk_blacklisted_user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT 1 FROM blacklisted_users WHERE user_id = %s AND vk_blacklisted_user_id = %s",
                    (user_id, vk_blacklisted_user_id)
                )
                return cur.fetchone() is not None
        except psycopg2.Error as e:
             logging.error(f"Ошибка при проверке пользователя в черном списке: {e}")
             return False
        finally:
            conn.close()
    return False

def get_max_search_result_id(user_id):
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT MAX(id) FROM search_results WHERE user_id = %s",
                    (user_id,)
                )
                max_id = cur.fetchone()[0]
                if max_id:
                    logging.info(f"Максимальный id  {max_id}  для пользователя {user_id} получен из БД")
                    return max_id
                else:
                    logging.info(f"Результаты поиска пользователя {user_id} в БД не найдены")
                    return None
        except psycopg2.Error as e:
            logging.error(f"Ошибка получения максимального id из БД: {e}")
            return None
        finally:
            conn.close()
    return None
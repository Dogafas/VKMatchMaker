# test_db.py
import psycopg2
import logging
from toolkit import get_db_connection_params

# Настройка логгирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def test_db_connection():
    """Тестирует подключение к базе данных PostgreSQL."""
    try:
        db_user, db_password, db_name, db_host, db_port = get_db_connection_params()

        # Вывод параметров подключения для проверки
        logging.info(f"DB User: {db_user}")
        logging.info(f"DB Password: {db_password}")
        logging.info(f"DB Name: {db_name}")
        logging.info(f"DB Host: {db_host}")
        logging.info(f"DB Port: {db_port}")

        # Строка подключения (DSN)
        dsn = f"postgresql://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"

        # Подключение к базе данных
        with psycopg2.connect(dsn, client_encoding='utf-8') as conn:
            logging.info("Успешное подключение к PostgreSQL!")

            # Дополнительная проверка: выполнить простой запрос
            with conn.cursor() as cursor:
                cursor.execute("SELECT 1;")
                result = cursor.fetchone()
                if result and result[0] == 1:
                    logging.info("Запрос к базе данных выполнен успешно.")
                else:
                    logging.error("Запрос к базе данных не удался.")
                    return False

        return True

    except psycopg2.Error as e:
        logging.error(f"Ошибка подключения к PostgreSQL: {e}")
        return False

if __name__ == "__main__":
    if test_db_connection():
        print("Тест подключения к базе данных пройден!")
    else:
        print("Проверка соединения с базой данных не удалась!")
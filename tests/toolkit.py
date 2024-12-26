"""Модуль содержит вспомогательные функции"""
# toolkit.py
import os
import logging
from dotenv import load_dotenv

load_dotenv()


def get_db_connection_params():
    """Получает параметры подключения к PostgreSQL из переменных окружения и проверяет их на валидность."""
    db_user = os.getenv("POSTGRES_USER")
    db_password = os.getenv("POSTGRES_PASSWORD")
    db_name = os.getenv("POSTGRES_DB")
    db_host = os.getenv("POSTGRES_HOST")
    db_port = os.getenv("POSTGRES_PORT")

    # Функция для проверки, что все символы в строке являются ASCII
    def is_ascii(text):
        try:
           text.encode('ascii')
           return True
        except UnicodeEncodeError:
           return False
       
    # Проверка каждого параметра на валидность
    if not is_ascii(db_user):
        logging.error(f"Invalid characters found in DB User: {db_user}")
        raise ValueError("Invalid characters in DB User")
    if not is_ascii(db_password):
        logging.error(f"Invalid characters found in DB Password: {db_password}")
        raise ValueError("Invalid characters in DB Password")
    if not is_ascii(db_name):
        logging.error(f"Invalid characters found in DB Name: {db_name}")
        raise ValueError("Invalid characters in DB Name")
    if not is_ascii(db_host):
        logging.error(f"Invalid characters found in DB Host: {db_host}")
        raise ValueError("Invalid characters in DB Host")
    #Порт не проверяем. Он должен быть числом.
    return db_user, db_password, db_name, db_host, db_port
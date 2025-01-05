import vk_api
from dotenv import load_dotenv
import os

load_dotenv()

# Настраиваем логирование

# Получаем токены и ID из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")


def search_users(offset=0, count=1):
    """Ищет пользователей по заданным критериям."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()

    sex = "female"
    age_from, age_to = None, None
    age_range = "18-25"
    city = 1
    if age_range == "18-25":
        age_from, age_to = 18, 25
    elif age_range == "25-35":
        age_from, age_to = 25, 35
    elif age_range == "35-45":
        age_from, age_to = 35, 45
    elif age_range == "45+":
        age_from = 45

    search_params = {
    "count": count,
    "fields": "photo_max_orig,city",  # Добавляем 'city'
    "sex": 1 if sex == "female" else 2 if sex == "male" else 0,
    "age_from": age_from,
    "age_to": age_to,
    "has_photo": 1,
    "offset": offset,
    "city": city,
    }

    users = vk.users.search(**search_params)
    return users["items"]


print(search_users())

import vk_api
from dotenv import load_dotenv
import os
import json
import time
import logging 
from vk_api.longpoll import VkLongPoll, VkEventType
from keyboards import get_sex_keyboard, get_age_keyboard, get_next_prev_keyboard, get_yes_no_keyboard

load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s') 


# Получаем токен и ID пользователя из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")

user_search_params = {}
user_search_results = {}

def get_user_info(user_id):
    """Получает информацию о пользователе и его фотографии."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    try:
        # Получаем основную информацию о пользователе, включая город
        user = vk.users.get(user_ids=user_id, fields="photo_max_orig,city")[0]
        first_name = user["first_name"]
        last_name = user["last_name"]
        profile_url = f"vk.com/id{user_id}"
        photo_url = user["photo_max_orig"]
        city_id = user.get("city", {}).get("id")
        logging.info(f"Получен city_id: {city_id}") 
        # Получаем название города
        city_name = "Не указан"
        if "city" in user:
            city_id = user["city"]["id"]
            city_info = vk.database.getCitiesById(city_ids=city_id)
            if city_info:
                city_name = city_info[0]["title"]

        # Получаем фотографии пользователя
        photos = vk.photos.get(owner_id=user_id, album_id="profile", count=3)
        attachments = []
        for photo in photos["items"]:
            attachments.append(f"photo{photo['owner_id']}_{photo['id']}")

        return {
            "first_name": first_name,
            "last_name": last_name,
            "profile_url": profile_url,
            "photo_url": photo_url,
            "city": city_name,
            "city_id": city_id,
            "attachments": attachments,
        }
    except vk_api.exceptions.ApiError as error:
        logging.error(f"Произошла ошибка: {error}")  
        return None


def send_message_from_group(user_id, message, attachments=None, keyboard=None):
    """Отправляет сообщение пользователю от имени сообщества."""
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    try:
        logging.info(f"Отправка сообщения пользователю {user_id} с клавиатурой: {keyboard}")  
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=vk_api.utils.get_random_id(),
            attachment=','.join(attachments) if attachments else None,
            keyboard=keyboard
        )
        logging.info(f"Сообщение успешно отправлено пользователю {user_id}")  
    except vk_api.exceptions.ApiError as error:
        if error.code == 901:
            logging.warning(f"Ошибка при отправке сообщения пользователю {user_id}: " 
                  f"Пользователь не разрешил сообщения от сообщества.")
        else:
           logging.error(f"Ошибка при отправке сообщения: {error}")  

def search_users(user_id, offset=0, count=1):
    """Ищет пользователей по заданным критериям."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    params = user_search_params.get(user_id, {})
    if not params:
        return "Необходимо указать параметры поиска"
    
    sex = params.get("sex")
    age_from, age_to = None, None
    age_range = params.get("age")
    city = params.get("city_id")
    if age_range == "18-25":
        age_from, age_to = 18, 25
    elif age_range == "25-35":
        age_from, age_to = 25, 35
    elif age_range == "35-45":
        age_from, age_to = 35, 45
    elif age_range == "45+":
        age_from = 45
    
    try:
      search_params = {
        "count": count,
        "fields": "photo_max_orig",
        "sex": 1 if sex == "female" else 2 if sex == "male" else 0,
        "age_from": age_from,
        "age_to": age_to,
        "has_photo": 1,
        "offset": offset,
        "city": city
    }
    
      users = vk.users.search(**search_params)
      return users["items"]
    except vk_api.exceptions.ApiError as error:
        logging.error(f"Ошибка при поиске пользователей: {error}")  
        return None

def handle_message(event, vk):
    """Обрабатывает входящие сообщения и отвечает на нажатия кнопок."""
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        message_text = event.text
        payload = event.extra_values.get('payload')
        logging.info(f"Получен payload: {payload}")  
    
        if payload:
            logging.info("Обработка payload...")  
            try:
                payload = json.loads(payload)
                button = payload.get('button')
                if button == "yes":
                    logging.info("Отправка ответа на кнопку 'Да' с клавиатурой...") 
                    send_message_from_group(user_id, "Отлично, продолжаем!", keyboard=get_sex_keyboard())
                elif button == "no":
                    logging.info("Отправка ответа на кнопку 'Нет' с клавиатурой...") 
                    send_message_from_group(user_id, "Жаль, тогда в другой раз.", keyboard=None)
                elif button == "male":
                     logging.info("Отправка запроса на выбор возраста") 
                     user_data = get_user_info(user_id)  
                     if user_data and user_data.get('city_id'): 
                         user_search_params[user_id] = {"sex": "male", "city_id": user_data['city_id']} 
                         logging.info(f"Сохраненные параметры поиска: {user_search_params.get(user_id)}")  
                     else:
                           logging.warning(f"Не удалось получить ID города")  
                           send_message_from_group(user_id, f"Не удалось получить ID города", keyboard=None)  
                     send_message_from_group(user_id, "Какой возраст предпочитаете?", keyboard=get_age_keyboard())
                elif button == "female":
                    logging.info("Отправка запроса на выбор возраста")  
                    user_data = get_user_info(user_id)  
                    if user_data and user_data.get('city_id'): 
                        user_search_params[user_id] = {"sex": "female", "city_id": user_data['city_id']}  
                        logging.info(f"Сохраненные параметры поиска: {user_search_params.get(user_id)}") 
                    else:
                           logging.warning(f"Не удалось получить ID города") 
                           send_message_from_group(user_id, f"Не удалось получить ID города", keyboard=None)  

                    send_message_from_group(user_id, "Какой возраст предпочитаете?", keyboard=get_age_keyboard())
                elif button in ["18-25", "25-35", "35-45", "45+"]:
                    logging.info(f"Выбран возраст: {button}")  
                    if user_id in user_search_params:
                         user_search_params[user_id]["age"] = button
                    
                    users = search_users(user_id, count=1)
                    if users:
                       user_search_results[user_id] = {
                           "results": users,
                           "current_index": 0
                       }
                       user = users[0]
                       if isinstance(user, dict):
                            if "first_name" in user and "last_name" in user and "id" in user:
                                message = (
                                    f"{user['first_name']} {user['last_name']}\n"
                                    f"vk.com/id{user['id']}\n"
                                 )
                                send_message_from_group(user_id, message, keyboard=get_next_prev_keyboard())
                            else:
                                logging.warning(f"У пользователя {user.get('id', 'неизвестен')} отсутствуют необходимые данные")  
                                send_message_from_group(user_id, f"У пользователя {user.get('id', 'неизвестен')} отсутствуют необходимые данные", keyboard=None)
                       else:
                           logging.warning(f"Не удалось получить данные о пользователе: {user}")
                           send_message_from_group(user_id, f"Не удалось получить данные о пользователе: {user}", keyboard=None)

                    else:
                       send_message_from_group(user_id, "Не удалось найти пользователей по заданным параметрам.", keyboard=None)
                elif button == "next" or button == "prev":
                    if user_id in user_search_results:
                        results = user_search_results[user_id]["results"]
                        current_index = user_search_results[user_id]["current_index"]
                        if button == "next":
                            current_index = min(current_index + 1, len(results) - 1)
                        elif button == "prev":
                             current_index = max(current_index - 1, 0)
                        user_search_results[user_id]["current_index"] = current_index
                        user = results[current_index]
                        if isinstance(user, dict):
                            if "first_name" in user and "last_name" in user and "id" in user:
                                message = (
                                    f"{user['first_name']} {user['last_name']}\n"
                                    f"vk.com/id{user['id']}\n"
                                )
                                send_message_from_group(user_id, message, keyboard=get_next_prev_keyboard())
                            else:
                                logging.warning(f"У пользователя {user.get('id', 'неизвестен')} отсутствуют необходимые данные")  
                                send_message_from_group(user_id, f"У пользователя {user.get('id', 'неизвестен')} отсутствуют необходимые данные", keyboard=None)
                        else:
                            logging.warning(f"Не удалось получить данные о пользователе: {user}") 
                            send_message_from_group(user_id, f"Не удалось получить данные о пользователе: {user}", keyboard=None)
                    
                    else:
                         send_message_from_group(user_id, "Нет результатов поиска, начните заново", keyboard=None)
                else:
                    send_message_from_group(user_id, "Неизвестная команда.", keyboard=None)
            except json.JSONDecodeError:
                 logging.error("Ошибка в payload.")  
                 send_message_from_group(user_id, "Ошибка в payload.", keyboard=None)
        
            
        if message_text == "Начать":
                logging.info("Обработка сообщения 'Начать'...")
                user_data = get_user_info(user_id)
                if user_data:
                    message = (
                        f"Привет, {user_data['first_name']} {user_data['last_name']}!\n"
                        f"Твой профиль: {user_data['profile_url']}\n"
                        f"Твой город: {user_data['city']}\n"
                        f"Хочешь продолжить?"
                    )
                    keyboard = get_yes_no_keyboard()
                    logging.info("Отправка приветственного сообщения с клавиатурой...")  
                    send_message_from_group(user_id, message, user_data["attachments"], keyboard=keyboard)
                

if __name__ == '__main__':
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    logging.info("Бот запущен")  
    try:
        for event in longpoll.listen():
            handle_message(event, vk)
    except Exception as e:
        logging.error(f"Бот упал с ошибкой: {e}")  
import vk_api
from dotenv import load_dotenv
import os
import json
import logging
from vk_api.longpoll import VkLongPoll, VkEventType
from keyboards import get_sex_keyboard, get_age_keyboard, get_next_prev_keyboard, get_yes_no_keyboard
from database import save_user, get_user_id, save_search_result, get_db_connection, is_search_result_exists, update_user_offset, update_user_last_viewed_result_id, get_max_search_result_id # <-ЗДЕСЬ ИЗМЕНЕНИЯ (импорт новых функций)

load_dotenv()

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Получаем токены и ID из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")

def get_user_info(user_id):
    """Получает информацию о пользователе, его фотографии и лайки к ним."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    try:
        # Получаем основную информацию о пользователе
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

        # Получаем все фотографии пользователя из альбома 'profile'
        all_photos = vk.photos.get(owner_id=user_id, album_id="profile", extended=1)
        if all_photos.get('items'):
            photos_with_likes = []
            for photo in all_photos["items"]:
                likes_info = vk.likes.getList(type="photo", owner_id=photo["owner_id"], item_id=photo["id"])
                likes_count = likes_info['count']
                photos_with_likes.append({
                    "attachment": f"photo{photo['owner_id']}_{photo['id']}",
                    "likes": likes_count
                })
            
            # Сортируем фотографии по количеству лайков (убывание)
            sorted_photos = sorted(photos_with_likes, key=lambda x: x["likes"], reverse=True)
            
            # Берем топ-3 фотографии
            top_photos = [item["attachment"] for item in sorted_photos[:3]]
        
            return {
                "first_name": first_name,
                "last_name": last_name,
                "profile_url": profile_url,
                "photo_url": photo_url,
                "city": city_name,
                "city_id": city_id,
                "attachments": top_photos,
            }
        else:
            return {
                "first_name": first_name,
                "last_name": last_name,
                "profile_url": profile_url,
                "photo_url": photo_url,
                "city": city_name,
                "city_id": city_id,
                "attachments": [],
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


# def search_users(user_id, offset=0, count=1):
#     """Ищет пользователей по заданным критериям."""
#     vk_session = vk_api.VkApi(token=TOKEN)
#     vk = vk_session.get_api()
#     user_info = get_user_info(user_id)
#     if not user_info:
#         return "Не удалось получить информацию о пользователе"
    
#     sex = None
#     age_from, age_to = None, None
#     age_range = None
#     city = user_info.get("city_id")
    
#     try:
#        user_db_info = get_user_id(user_id)
#        if not user_db_info:
#            user_db_id = save_user(user_id, user_info["first_name"], user_info["last_name"], user_info["city"])
#            offset = 0
#        else:
#            user_db_id = user_db_info.get("id")
#            offset = user_db_info.get("offset")
#     except Exception as e:
#         logging.error(f"Ошибка при сохранении пользователя в БД: {e}")
#         return None
    
    
#     try:
#         if user_id in user_search_params:
#           sex = user_search_params[user_id].get("sex")
#           age_range = user_search_params[user_id].get("age")
#         if age_range == "18-25":
#             age_from, age_to = 18, 25
#         elif age_range == "26-35":
#             age_from, age_to = 26, 35
#         elif age_range == "36-45":
#             age_from, age_to = 36, 45
#         elif age_range == "45+":
#             age_from = 46
        
#         search_params = {
#             "count": count,
#             "fields": "photo_max_orig",
#             "sex": 1 if sex == "female" else 2 if sex == "male" else 0,
#             "age_from": age_from,
#             "age_to": age_to,
#             "has_photo": 1,
#             "offset": offset,
#             "city": city
#         }
#         users = vk.users.search(**search_params)
#         return users["items"]
#     except vk_api.exceptions.ApiError as error:
#         logging.error(f"Ошибка при поиске пользователей: {error}")
#         return None

def search_users(user_id, offset=0, count=1):
    """Ищет пользователей по заданным критериям."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    user_info = get_user_info(user_id)
    if not user_info:
        return "Не удалось получить информацию о пользователе"
    
    sex = None
    age_from, age_to = None, None
    age_range = None
    city = user_info.get("city_id")
    
    try:
       user_db_info = get_user_id(user_id)
       if not user_db_info:
           user_db_id = save_user(user_id, user_info["first_name"], user_info["last_name"], user_info["city"])
           offset = 0
       else:
           user_db_id = user_db_info.get("id")
           offset = user_db_info.get("offset")
    except Exception as e:
        logging.error(f"Ошибка при сохранении пользователя в БД: {e}")
        return None
    
    
    try:
        if user_id in user_search_params:
          sex = user_search_params[user_id].get("sex")
          age_range = user_search_params[user_id].get("age")
        if age_range == "18-25":
            age_from, age_to = 18, 25
        elif age_range == "26-35":
            age_from, age_to = 26, 35
        elif age_range == "36-45":
            age_from, age_to = 36, 45
        elif age_range == "45+":
            age_from = 46
        
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
        
        filtered_users = [] # <-ЗДЕСЬ ИЗМЕНЕНИЯ (новый список для открытых профилей)
        for user in users["items"]:
            if user.get("photo_max_orig"): # <-ЗДЕСЬ ИЗМЕНЕНИЯ (проверяем наличие фото)
                filtered_users.append(user) # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавляем пользователя в список если фото есть)
        
        return filtered_users # <-ЗДЕСЬ ИЗМЕНЕНИЯ (возвращаем отфильтрованный список)
    except vk_api.exceptions.ApiError as error:
        logging.error(f"Ошибка при поиске пользователей: {error}")
        return None

user_search_params = {}

def handle_message(event, vk):
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
                        user_search_params[user_id] = {"sex": "male"}
                        logging.info(f"Сохраненные параметры поиска: {user_search_params.get(user_id)}")
                     else:
                           logging.warning(f"Не удалось получить ID города")
                           send_message_from_group(user_id, f"Не удалось получить ID города", keyboard=None)
                     send_message_from_group(user_id, "Какой возраст предпочитаете?", keyboard=get_age_keyboard())
                elif button == "female":
                    logging.info("Отправка запроса на выбор возраста")
                    user_data = get_user_info(user_id)
                    if user_data and user_data.get('city_id'):
                         user_search_params[user_id] = {"sex": "female"}
                         logging.info(f"Сохраненные параметры поиска: {user_search_params.get(user_id)}")
                    else:
                           logging.warning(f"Не удалось получить ID города")
                           send_message_from_group(user_id, f"Не удалось получить ID города", keyboard=None)

                    send_message_from_group(user_id, "Какой возраст предпочитаете?", keyboard=get_age_keyboard())
                elif button in ["18-25", "26-35", "36-45", "45+"]:
                    logging.info(f"Выбран возраст: {button}")
                    if user_id in user_search_params:
                        user_search_params[user_id]["age"] = button
                    
                    users = search_users(user_id, count=1)
                    if users:
                        user_db_info = get_user_id(user_id)
                        if not user_db_info:
                           user_info = get_user_info(user_id)
                           user_db_id = save_user(user_id, user_info["first_name"], user_info["last_name"], user_info["city"])
                           offset = 0
                        else:
                            user_db_id = user_db_info.get("id")
                            offset = user_db_info.get("offset")
                        
                        new_user = None
                        for user in users:
                            if not is_search_result_exists(user_db_id, user["id"]):
                                found_user_info = get_user_info(user["id"])
                                if found_user_info:
                                    save_search_result(user_db_id, user["id"], found_user_info["first_name"], found_user_info["last_name"], f"vk.com/id{user['id']}")
                                    new_user = user
                                    offset += 1
                                    break
                        
                        if new_user:
                            found_user_info = get_user_info(new_user["id"])
                            if found_user_info:
                                message = (
                                    f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                                    f"vk.com/id{new_user['id']}\n"
                                    f"Город: {found_user_info['city']}\n"
                                )
                                update_user_offset(user_id, offset)
                                update_user_last_viewed_result_id(user_id, None) # <-ЗДЕСЬ ИЗМЕНЕНИЯ (устанавливаем last_viewed_result_id в None при новом поиске)
                                send_message_from_group(user_id, message, found_user_info["attachments"], keyboard=get_next_prev_keyboard())
                            else:
                                logging.warning(f"Не удалось получить данные о пользователе: {new_user.get('id', 'неизвестен')}")
                                send_message_from_group(user_id, f"Не удалось получить данные о пользователе: {new_user.get('id', 'неизвестен')}", keyboard=None)
                        else:
                            send_message_from_group(user_id, "Нет новых анкет.", keyboard=None)
                    else:
                       send_message_from_group(user_id, "Не удалось найти пользователей по заданным параметрам.", keyboard=None)
                elif button == "next":
                    user_db_info = get_user_id(user_id)
                    if user_db_info:
                        user_db_id = user_db_info.get("id")
                        offset = user_db_info.get("offset")
                        users = search_users(user_id,offset, count = 1)
                        if users:
                            new_user = None
                            for user in users:
                                if not is_search_result_exists(user_db_id, user["id"]): # <-ЗДЕСЬ ИЗМЕНЕНИЯ (проверка на существование анкеты)
                                    found_user_info = get_user_info(user["id"])
                                    if found_user_info:
                                       save_search_result(user_db_id, user["id"], found_user_info["first_name"], found_user_info["last_name"], f"vk.com/id{user['id']}") # <-ЗДЕСЬ ИЗМЕНЕНИЯ (сохранение анкеты)
                                       new_user = user
                                       offset += 1
                                       break
                            
                            if new_user:
                                found_user_info = get_user_info(new_user["id"])
                                if found_user_info:
                                    message = (
                                        f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                                        f"vk.com/id{new_user['id']}\n"
                                        f"Город: {found_user_info['city']}\n"
                                    )
                                    update_user_offset(user_id, offset)
                                    last_viewed_result_id = user_db_info.get("last_viewed_result_id")
                                    if last_viewed_result_id == None:
                                         max_id = get_max_search_result_id(user_db_id)
                                         update_user_last_viewed_result_id(user_id, max_id)
                                    send_message_from_group(user_id, message, found_user_info["attachments"], keyboard=get_next_prev_keyboard())
                                else:
                                    logging.warning(f"Не удалось получить данные о пользователе: {new_user.get('id', 'неизвестен')}")
                                    send_message_from_group(user_id, f"Не удалось получить данные о пользователе: {new_user.get('id', 'неизвестен')}", keyboard=None)
                            else:
                                send_message_from_group(user_id, "Нет новых анкет.", keyboard=None)
                        else:
                            send_message_from_group(user_id, "Нет новых анкет.", keyboard=None)
                    else:
                        send_message_from_group(user_id, "Пользователь не найден в базе данных, начните заново (напишите: Начать)", keyboard=None)
                elif button == "prev":
                   user_db_info = get_user_id(user_id)
                   if user_db_info:
                        user_db_id = user_db_info.get("id")
                        last_viewed_result_id = user_db_info.get("last_viewed_result_id")
                        if last_viewed_result_id is None:
                            max_id = get_max_search_result_id(user_db_id)
                            if max_id:
                                 cur_id = max_id
                            else:
                                 send_message_from_group(user_id, "Нет результатов поиска, начните заново (напишите: Начать)", keyboard=None)
                                 return
                        else:
                           cur_id = last_viewed_result_id - 1
                        if cur_id > 0:
                            with get_db_connection().cursor() as cur:
                                cur.execute(
                                   "SELECT vk_search_user_id FROM search_results WHERE id = %s AND user_id = %s",
                                     (cur_id,user_db_id)
                                )
                                result = cur.fetchone()
                                if result:
                                    found_user_info = get_user_info(result[0])
                                    if found_user_info:
                                       message = (
                                            f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                                            f"vk.com/id{result[0]}\n"
                                            f"Город: {found_user_info['city']}\n"
                                        )
                                       update_user_last_viewed_result_id(user_id, cur_id)
                                       send_message_from_group(user_id, message, found_user_info["attachments"], keyboard=get_next_prev_keyboard())
                                    else:
                                       logging.warning(f"Не удалось получить данные о пользователе: {result[0]}")
                                       send_message_from_group(user_id, f"Не удалось получить данные о пользователе: {result[0]}", keyboard=None)
                                else:
                                    send_message_from_group(user_id, "Нет предыдущих анкет.", keyboard=None)
                        else:
                            send_message_from_group(user_id, "Нет предыдущих анкет.", keyboard=None)
                   else:
                        send_message_from_group(user_id, "Пользователь не найден в базе данных, начните заново (напишите: Начать)", keyboard=None)
                else:
                    send_message_from_group(user_id, "Неизвестная команда.", keyboard=None)
            except json.JSONDecodeError:
                 logging.error("Ошибка в payload.")
                 send_message_from_group(user_id, "Ошибка в payload.", keyboard=None)
        if message_text.lower() == "начать":
                logging.info("Обработка сообщения 'Начать'...")
                user_data = get_user_info(user_id)
                if user_data:
                     message = (
                        f"Привет, {user_data['first_name']} {user_data['last_name']}!\n"
                        f"Твой профиль: {user_data['profile_url']}\n"
                        f"Твой город: {user_data['city']}\n"
                        f"Хочешь продолжить? (жми ДА или НЕТ ↓↓↓)"
                    )
                     keyboard = get_yes_no_keyboard()
                     logging.info("Отправка приветственного сообщения с клавиатурой...")
                     send_message_from_group(user_id, message, user_data["attachments"], keyboard=keyboard)
                else:
                    send_message_from_group(user_id, "Не удалось получить информацию о пользователе.", keyboard=None)

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
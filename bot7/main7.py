# main7.py
import vk_api
from dotenv import load_dotenv
import os
import json
import logging
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.exceptions import ApiError

from keyboards import (
    get_sex_keyboard,
    get_age_keyboard,
    get_next_prev_keyboard,
    get_yes_no_keyboard,
)
from db_requests import (
    set_user,
    save_search_results,
    get_search_results,
    set_favorite,
    set_blacklist,
    get_favourite_list,
    get_search_result_by_id, # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (импортируем функцию get_search_result_by_id)
)

load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

# Получаем токены и ID из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")
search_params = {}


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
        all_photos = vk.photos.get(
            owner_id=user_id, album_id="profile", extended=1, photo_sizes=1 # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавил параметр photo_sizes=1)
        )
        if all_photos.get("items"):
            photos_with_sizes = [] # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (изменил название переменной)
            for photo in all_photos["items"]:
                if "sizes" in photo: # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавил проверку на существование 'sizes' в ответе 'photo')
                    max_size_url = None
                    max_size = 0
                    for size in photo["sizes"]:
                         if size["type"] in ["x", "z", "y"]:
                            if size["width"] * size["height"] > max_size:
                                max_size = size["width"] * size["height"]
                                max_size_url = size["url"]
                    if max_size_url:
                        photos_with_sizes.append({ # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (изменил название переменной)
                            "attachment": f"photo{photo['owner_id']}_{photo['id']}",
                             "likes": photo.get('likes', {}).get('count', 0), # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (получаем количество лайков)
                            "max_size_url": max_size_url,
                        })
                
            # Сортируем фотографии по количеству лайков (убывание)
            sorted_photos = sorted(
                photos_with_sizes, key=lambda x: x["likes"], reverse=True # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сортируем по количеству лайков)
            )

            # Берем топ-3 фотографии
            top_photos = [
                item["attachment"] for item in sorted_photos[:3]
            ]

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
        logging.info(
            f"Отправка сообщения пользователю {user_id} с клавиатурой: {keyboard}"
        )
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=vk_api.utils.get_random_id(),
            attachment=",".join(attachments) if attachments else None,
            keyboard=keyboard,
        )
        logging.info(f"Сообщение успешно отправлено пользователю {user_id}")
    except vk_api.exceptions.ApiError as error:
        if error.code == 901:
            logging.warning(
                f"Ошибка при отправке сообщения пользователю {user_id}: "
                f"Пользователь не разрешил сообщения от сообщества."
            )
        else:
            logging.error(f"Ошибка при отправке сообщения: {error}")


def search_users(user_id, offset=0, count=1):
    """Ищет пользователей по заданным критериям."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    
    if not search_params:
        return "Необходимо указать параметры поиска"

    sex = search_params.get("sex")
    age_from, age_to = None, None
    age_range = search_params.get("age")
    city = search_params.get("city_id")
    if age_range == "18-25":
        age_from, age_to = 18, 25
    elif age_range == "26-35":
        age_from, age_to = 26, 35
    elif age_range == "36-44":
        age_from, age_to = 36, 44
    elif age_range == "45+":
        age_from = 45

    saved_results = get_search_results(user_id)
    saved_user_ids = {result.result_user_id for result in saved_results}

    found_users = []
    search_params_vk = {
        "count": count,
        "fields": "photo_max_orig, city",
        "sex": 1 if sex == "female" else 2 if sex == "male" else 0,
        "age_from": age_from,
        "age_to": age_to,
        "has_photo": 1,
        "offset": offset,
        "city": city,
    }
    while len(found_users) < count:
        try:
            users = vk.users.search(**search_params_vk)
            if not users['items']:
                break
            for user in users['items']:
                if not user.get('is_closed') and user['id'] not in saved_user_ids:
                    found_users.append(user)
                    if len(found_users) == count:
                        break
            search_params_vk['offset'] += len(users['items'])
        except vk_api.exceptions.ApiError as error:
            logging.error(f"Ошибка при поиске пользователей: {error}")
            return None
    return found_users


def _handle_yes_button(user_id):
    logging.info("Отправка ответа на кнопку 'Да' с клавиатурой...")
    send_message_from_group(
        user_id, "Отлично, продолжаем!", keyboard=get_sex_keyboard()
    )


def _handle_no_button(user_id):
    logging.info("Отправка ответа на кнопку 'Нет' с клавиатурой...")
    send_message_from_group(user_id, "Жаль, тогда в другой раз.", keyboard=None)


def _handle_sex_button(user_id, sex):
    global search_params
    logging.info(f"Отправка запроса на выбор возраста, выбран пол: {sex}")
    user_data = get_user_info(user_id)
    if user_data and user_data.get("city_id"):
        search_params = {
            "sex": sex,
            "age": 0,
            "city_id": user_data["city_id"],
        }
        logging.info(
            f"Сохраненные параметры поиска: {search_params}"
        )
    else:
        logging.warning(f"Не удалось получить ID города")
        send_message_from_group(
            user_id, f"Не удалось получить ID города", keyboard=None
        )
    send_message_from_group(
        user_id,
        "Какой возраст предпочитаете?",
        keyboard=get_age_keyboard(),
    )


def _handle_age_button(user_id, age):
    global search_params
    logging.info(f"Выбран возраст: {age}")
    if search_params:
       search_params["age"] = age
    _show_next_user(user_id)


def _show_next_user(user_id):
    users = search_users(user_id, count=1)
    if users:
        for user in users:
            found_user_info = get_user_info(user["id"])
            if found_user_info: # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавил проверку на found_user_info)
                save_search_results(
                user_id,
                user["id"],
                found_user_info["first_name"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение first_name)
                found_user_info["last_name"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение last_name)
                found_user_info["profile_url"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение profile_url)
                )
                search_results = get_search_results(user_id)
                current_search_result = search_results[-1]
                message = (
                    f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                    f"vk.com/id{users[0]['id']}\n"
                    f"Город: {found_user_info['city']}\n"
                )
                send_message_from_group(
                    user_id,
                    message,
                    found_user_info["attachments"],
                    keyboard=get_next_prev_keyboard(current_search_result.id),
                )
            else:
                logging.warning(
                    f"Не удалось получить данные о пользователе: {users[0].get('id', 'неизвестен')}"
                )
                send_message_from_group(
                    user_id,
                    f"Не удалось получить данные о пользователе: {users[0].get('id', 'неизвестен')}",
                    keyboard=None,
                )
    else:
        send_message_from_group(
            user_id,
            "Не удалось найти пользователей по заданным параметрам.",
            keyboard=None,
        )


def _handle_search_button(user_id, search_result_id):
    users = search_users(user_id, count=1)
    if users:
        search_user_data = users[0]
        found_user_info = get_user_info(search_user_data["id"])
        if found_user_info: # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавил проверку на found_user_info)
            save_search_results(
                user_id,
                search_user_data["id"],
                found_user_info["first_name"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение first_name)
                found_user_info["last_name"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение last_name)
                found_user_info["profile_url"], # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (сохранение profile_url)
            )
            search_results = get_search_results(user_id)
            current_search_result = search_results[-1]
            message = (
                f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                f"vk.com/id{search_user_data['id']}\n"
                f"Город: {found_user_info['city']}\n"
            )
            send_message_from_group(
                user_id, message,
                found_user_info["attachments"],
                keyboard=get_next_prev_keyboard(current_search_result.id),
            )
            print(
                save_search_results(
                    user_id, search_user_data["id"], found_user_info["first_name"], found_user_info["last_name"], found_user_info["profile_url"] # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (передача first_name, last_name, profile_url)
                )
            )
    else:
        send_message_from_group(
            user_id, "Не удалось найти следующего пользователя",
            keyboard=get_next_prev_keyboard(search_result_id),
        )


def _handle_prev_button(user_id, search_result_id):
    search_results = get_search_results(user_id)
    if search_results:
        prev_result = None
        for i, result in enumerate(search_results):
            if result.id == search_result_id:
                if i > 0:
                  prev_result = search_results[i-1]
                  break
        if prev_result:
            result_user_id = prev_result.result_user_id
            found_user_info = get_user_info(
                result_user_id
            )
            message = (
                f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                f"vk.com/id{result_user_id}\n"
                f"Город: {found_user_info['city']}\n"
            )
            send_message_from_group(
                user_id,
                message,
                found_user_info["attachments"],
                keyboard=get_next_prev_keyboard(prev_result.id),
            )
        else:
            send_message_from_group(
                user_id,
                "Не удалось найти предыдущего пользователя",
                keyboard=get_next_prev_keyboard(search_result_id),
            )
    else:
        send_message_from_group(
            user_id,
            "К сожалению, нет предыдущих пользователей",
            keyboard=get_next_prev_keyboard(search_result_id),
        )
def _handle_start_command(user_id):
    logging.info("Обработка сообщения 'Начать'...")
    user_data = get_user_info(user_id)

    print(set_user(user_id))
    if user_data:
        message = (
            f"Привет, {user_data['first_name']} {user_data['last_name']}!\n"
            f"Твой профиль: {user_data['profile_url']}\n"
            f"Твой город: {user_data['city']}\n"
            f"Хочешь продолжить? (жми ДА или НЕТ) ?"
        )
        keyboard = get_yes_no_keyboard()
        logging.info("Отправка приветственного сообщения с клавиатурой...")
        send_message_from_group(
            user_id, message, user_data["attachments"], keyboard=keyboard
        )

def _handle_favorite_button(user_id, search_result_id):
    search_result = get_search_result_by_id(search_result_id) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (получаем данные пользователя по id)
    if search_result:
        status = set_favorite(search_result_id)
        if status == "Favorite flag set to True":
            send_message_from_group(
                user_id, f"Пользователь {search_result.first_name} {search_result.last_name} добавлен в избранное!", keyboard=get_next_prev_keyboard(search_result_id) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавляем имя и фамилию в сообщение)
            )
        else:
            send_message_from_group(
                user_id, f"Пользователь {search_result.first_name} {search_result.last_name} удален из избранного!", keyboard=get_next_prev_keyboard(search_result_id)  # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавляем имя и фамилию в сообщение)
            )
    else:
        send_message_from_group(
            user_id, "Не удалось добавить пользователя в избранное.", keyboard=get_next_prev_keyboard(search_result_id)
        )


def _handle_blacklist_button(user_id, search_result_id):
    search_result = get_search_result_by_id(search_result_id) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (получаем данные пользователя по id)
    if search_result:
        status = set_blacklist(search_result_id)
        if status == "Blacklist flag set to True":
            send_message_from_group(
                user_id, f"Пользователь {search_result.first_name} {search_result.last_name} добавлен в черный список!", keyboard=get_next_prev_keyboard(search_result_id) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавляем имя и фамилию в сообщение)
            )
        else:
            send_message_from_group(
                user_id, f"Пользователь {search_result.first_name} {search_result.last_name} удален из черного списка!", keyboard=get_next_prev_keyboard(search_result_id) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавляем имя и фамилию в сообщение)
            )
    else:
        send_message_from_group(
            user_id, "Не удалось добавить пользователя в черный список.", keyboard=get_next_prev_keyboard(search_result_id)
        )

def _get_user_favourite_list(user_id, search_result_id):
    fav_list = get_favourite_list(user_id)
    if fav_list:
        message = ("Твой список избранных: \n" + 
                   "\n".join(f"{user.first_name} {user.last_name} (vk.com/id{user.result_user_id})" for user in fav_list)) # <-ЗДЕСЬ ИЗМЕНЕНИЯ: (добавляем имя и фамилию в список избранных)
        send_message_from_group(
            user_id, message, keyboard=get_next_prev_keyboard(search_result_id)
        )
    else:
        send_message_from_group(
            user_id, "В вашем списке избранных нет пользователей", keyboard=get_next_prev_keyboard(search_result_id)
        )

def handle_message(event, vk):
    """Обрабатывает входящие сообщения и отвечает на нажатия кнопок."""
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        message_text = event.text
        payload = event.extra_values.get("payload")
        logging.info(f"Получен payload: {payload}")

        if payload:
            try:
                payload = json.loads(payload)
                button = payload.get("button")
                search_result_id = payload.get("search_result_id")

                # Словарь для обработки кнопок
                button_handlers = {
                    "yes": _handle_yes_button,
                    "no": _handle_no_button,
                    "male": lambda user_id: _handle_sex_button(user_id, "male"),
                    "female": lambda user_id: _handle_sex_button(user_id, "female"),
                    "18-25": lambda user_id: _handle_age_button(user_id, "18-25"),
                    "26-35": lambda user_id: _handle_age_button(user_id, "26-35"),
                    "36-44": lambda user_id: _handle_age_button(user_id, "36-44"),
                    "45+": lambda user_id: _handle_age_button(user_id, "45+"),
                    "search": _handle_search_button,
                    "prev": _handle_prev_button,
                    "favorite": _handle_favorite_button,
                    "blacklist": _handle_blacklist_button,
                    "fav_list": _get_user_favourite_list
                }

                handler = button_handlers.get(button)
                if handler:
                    if button in ["yes", "no", "male", "female", "18-25", "26-35", "36-44", "45+"]:
                         handler(user_id)
                    else:
                        handler(user_id, search_result_id)
                else:
                    send_message_from_group(user_id, "Неизвестная команда.", keyboard=None)
            except json.JSONDecodeError:
                logging.error("Ошибка в payload.")
                send_message_from_group(user_id, "Ошибка в payload.", keyboard=None)
        elif message_text.lower() == "начать":
            _handle_start_command(user_id)
if __name__ == "__main__":
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    logging.info("Бот запущен")
    for event in longpoll.listen():
        handle_message(event, vk)
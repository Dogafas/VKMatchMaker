import vk_api
from dotenv import load_dotenv
import os
import sys
import json
import logging
from vk_api.longpoll import VkLongPoll, VkEventType
from keyboards import (
    get_sex_keyboard,
    get_age_keyboard,
    get_next_prev_keyboard,
    get_yes_no_keyboard,
)
from datetime import datetime

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))


load_dotenv()

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


# Получаем токен и ID пользователя из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")

user_search_params = {}
user_search_results = {}


def calculate_age(bdate):
    birthdate = datetime.strptime(bdate, "%d.%m.%Y")
    today = datetime.today()
    age = (
        today.year
        - birthdate.year
        - ((today.month, today.day) < (birthdate.month, birthdate.day))
    )
    return age


def get_user_info(user_id):
    """Получает информацию о пользователе, его фотографии и лайки к ним."""
    vk_session = vk_api.VkApi(token=TOKEN)
    vk = vk_session.get_api()
    try:
        # Получаем основную информацию о пользователе
        user = vk.users.get(user_ids=user_id, fields="photo_max_orig,city,bdate")[0]
        first_name = user["first_name"]
        last_name = user["last_name"]
        age = calculate_age(user["bdate"])
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
            owner_id=user_id, album_id="profile", extended=1
        )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавил extended=1)
        if all_photos.get("items"):  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавил проверку наличия фото)
            photos_with_likes = []  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (инициализируем список)
            for photo in all_photos["items"]:  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (перебираем все фото)
                likes_info = vk.likes.getList(
                    type="photo", owner_id=photo["owner_id"], item_id=photo["id"]
                )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (получаем лайки)
                likes_count = likes_info[
                    "count"
                ]  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (считаем количество лайков)
                photos_with_likes.append(
                    {  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавляем словарь с информацией о фото и лайках)
                        "attachment": f"photo{photo['owner_id']}_{photo['id']}",
                        "likes": likes_count,
                    }
                )

            # Сортируем фотографии по количеству лайков (убывание)
            sorted_photos = sorted(
                photos_with_likes, key=lambda x: x["likes"], reverse=True
            )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (сортируем фотографии по лайкам)

            # Берем топ-3 фотографии
            top_photos = [
                item["attachment"] for item in sorted_photos[:3]
            ]  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (берем топ 3 фото)

            return {
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
                "profile_url": profile_url,
                "photo_url": photo_url,
                "city": city_name,
                "city_id": city_id,
                "attachments": top_photos,  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (возвращаем топ 3 фото)
            }
        else:  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (если фото нет, то возвращаем информацию без фото)
            return {
                "first_name": first_name,
                "last_name": last_name,
                "age": age,
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
            "city": city,
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
        payload = event.extra_values.get("payload")
        logging.info(f"Получен payload: {payload}")

        if payload:
            logging.info("Обработка payload...")
            try:
                payload = json.loads(payload)
                button = payload.get("button")
                if button == "yes":
                    logging.info("Отправка ответа на кнопку 'Да' с клавиатурой...")
                    send_message_from_group(
                        user_id, "Отлично, продолжаем!", keyboard=get_sex_keyboard()
                    )
                elif button == "no":
                    logging.info("Отправка ответа на кнопку 'Нет' с клавиатурой...")
                    send_message_from_group(
                        user_id, "Жаль, тогда в другой раз.", keyboard=None
                    )
                elif button == "male":
                    logging.info("Отправка запроса на выбор возраста")
                    user_data = get_user_info(user_id)
                    if user_data and user_data.get("city_id"):
                        user_search_params[user_id] = {
                            "sex": "male",
                            "city_id": user_data["city_id"],
                        }
                        logging.info(
                            f"Сохраненные параметры поиска: {user_search_params.get(user_id)}"
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
                elif button == "female":
                    logging.info("Отправка запроса на выбор возраста")
                    user_data = get_user_info(user_id)
                    if user_data and user_data.get("city_id"):
                        user_search_params[user_id] = {
                            "sex": "female",
                            "city_id": user_data["city_id"],
                        }
                        logging.info(
                            f"Сохраненные параметры поиска: {user_search_params.get(user_id)}"
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
                elif button in ["18-25", "25-35", "35-45", "45+"]:
                    logging.info(f"Выбран возраст: {button}")
                    if user_id in user_search_params:
                        user_search_params[user_id]["age"] = button

                    users = search_users(user_id, count=1)
                    if users:
                        user_search_results[user_id] = {
                            "results": users,
                            "current_index": 0,
                        }
                        user = users[0]
                        if isinstance(user, dict):
                            found_user_info = get_user_info(
                                user["id"]
                            )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (получаем информацию о пользователе)
                            if (
                                found_user_info
                            ):  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (проверка что данные получены)
                                message = (
                                    f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                                    f"vk.com/id{user['id']}\n"
                                    f"Город: {found_user_info['city']}\n"  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавляем город)
                                )
                                send_message_from_group(
                                    user_id,
                                    message,
                                    found_user_info["attachments"],
                                    keyboard=get_next_prev_keyboard(),
                                )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (передаем фото)
                            else:
                                logging.warning(
                                    f"Не удалось получить данные о пользователе: {user.get('id', 'неизвестен')}"
                                )
                                send_message_from_group(
                                    user_id,
                                    f"Не удалось получить данные о пользователе: {user.get('id', 'неизвестен')} ",
                                    keyboard=None,
                                )
                        else:
                            logging.warning(
                                f"Не удалось получить данные о пользователе: {user}"
                            )
                            send_message_from_group(
                                user_id,
                                f"Не удалось получить данные о пользователе: {user}",
                                keyboard=None,
                            )

                    else:
                        send_message_from_group(
                            user_id,
                            "Не удалось найти пользователей по заданным параметрам.",
                            keyboard=None,
                        )
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
                            found_user_info = get_user_info(
                                user["id"]
                            )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (получаем информацию о пользователе)
                            if (
                                found_user_info
                            ):  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (проверка что данные получены)
                                message = (
                                    f"{found_user_info['first_name']} {found_user_info['last_name']}\n"
                                    f"vk.com/id{user['id']}\n"
                                    f"Город: {found_user_info['city']}\n"  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (добавляем город)
                                )
                                send_message_from_group(
                                    user_id,
                                    message,
                                    found_user_info["attachments"],
                                    keyboard=get_next_prev_keyboard(),
                                )  # <-ЗДЕСЬ ИЗМЕНЕНИЯ (передаем фото)
                            else:
                                logging.warning(
                                    f"Не удалось получить данные о пользователе: {user.get('id', 'неизвестен')}"
                                )
                                send_message_from_group(
                                    user_id,
                                    f"Не удалось получить данные о пользователе: {user.get('id', 'неизвестен')}",
                                    keyboard=None,
                                )
                        else:
                            logging.warning(
                                f"Не удалось получить данные о пользователе: {user}"
                            )
                            send_message_from_group(
                                user_id,
                                f"Не удалось получить данные о пользователе: {user}",
                                keyboard=None,
                            )

                    else:
                        send_message_from_group(
                            user_id,
                            "Нет результатов поиска, начните заново (напишите: Начать)",
                            keyboard=None,
                        )
                else:
                    send_message_from_group(
                        user_id, "Неизвестная команда.", keyboard=None
                    )
            except json.JSONDecodeError:
                logging.error("Ошибка в payload.")
                send_message_from_group(user_id, "Ошибка в payload.", keyboard=None)

        if message_text.lower() == "начать":
            logging.info("Обработка сообщения 'Начать'...")
            user_data = get_user_info(user_id)

            message = (
                    f"Привет, {user_data['first_name']} {user_data['last_name']}!\n"
                    f"Твой профиль: {user_data['profile_url']}\n"
                    f"Твой город: {user_data['city']}\n"
                    f"Хочешь продолжить, жми ДА или НЕТ ?"
            )
            keyboard = get_yes_no_keyboard()
            logging.info("Отправка приветственного сообщения с клавиатурой...")
            send_message_from_group(
                user_id, message, user_data["attachments"], keyboard=keyboard
            )


if __name__ == "__main__":
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    logging.info("Бот запущен")
    try:
        for event in longpoll.listen():
            handle_message(event, vk)
    except Exception as e:
            logging.error(f"Бот упал с ошибкой: {e}")
    except KeyboardInterrupt:
        logging.info("Бот остановлен")
        sys.exit(0)

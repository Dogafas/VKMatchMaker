"""Две кнопки ДА-НЕТ"""
import vk_api
from dotenv import load_dotenv
import os
import json
from vk_api.longpoll import VkLongPoll, VkEventType

load_dotenv()

# Получаем токен и ID пользователя из переменных окружения
TOKEN = os.getenv("VKTOKEN")
USER_ID = os.getenv("VKUSER")
GROUP_TOKEN = os.getenv("VKTOKENGROUP")

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
            "attachments": attachments,
        }
    except vk_api.exceptions.ApiError as error:
        print(f"Произошла ошибка: {error}")
        return None

def create_keyboard():
    """Создает клавиатуру с двумя кнопками."""
    keyboard = {
        "one_time": False,
        "buttons": [
            [
                {
                    "action": {
                        "type": "text",
                        "label": "Да",
                        "payload": '{"button": "yes"}'
                    },
                    "color": "positive"
                },
                {
                    "action": {
                        "type": "text",
                        "label": "Нет",
                       "payload": '{"button": "no"}'
                    },
                    "color": "negative"
                }
             ]
           ]
        }
    keyboard_json = json.dumps(keyboard, ensure_ascii=False)
    print(f"Сформированная клавиатура: {keyboard_json}")
    return keyboard_json

def send_message_from_group(user_id, message, attachments=None, keyboard=None):
    """Отправляет сообщение пользователю от имени сообщества."""
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    try:
        print(f"Отправка сообщения пользователю {user_id} с клавиатурой: {keyboard}")
        vk.messages.send(
            user_id=user_id,
            message=message,
            random_id=vk_api.utils.get_random_id(),
            attachment=','.join(attachments) if attachments else None,
            keyboard=keyboard
        )
        print(f"Сообщение успешно отправлено пользователю {user_id}")
    except vk_api.exceptions.ApiError as error:
        if error.code == 901:
            print(f"Ошибка при отправке сообщения пользователю {user_id}: "
                  f"Пользователь не разрешил сообщения от сообщества.")
        else:
            print(f"Ошибка при отправке сообщения: {error}")


def handle_message(event, vk):
    """Обрабатывает входящие сообщения и отвечает на нажатия кнопок."""
    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
        user_id = event.user_id
        message_text = event.text
        payload = event.extra_values.get('payload')
        print(f"Получен payload: {payload}")


        if payload:
            print("Обработка payload...") 
            try:
                payload = json.loads(payload)
                button = payload.get('button')
                keyboard = create_keyboard()
                if button == "yes":
                    print("Отправка ответа на кнопку 'Да' с клавиатурой...") 
                    send_message_from_group(user_id, "Отлично, продолжаем!", keyboard=keyboard)
                elif button == "no":
                    print("Отправка ответа на кнопку 'Нет' с клавиатурой...") 
                    send_message_from_group(user_id, "Жаль, тогда в другой раз.", keyboard=keyboard)
                else:
                    send_message_from_group(user_id, "Неизвестная команда.", keyboard=None)
            except json.JSONDecodeError:
                send_message_from_group(user_id, "Ошибка в payload.", keyboard=None)
        
            
        if message_text == "Начать":  
                print("Обработка сообщения 'Начать'...") 
                user_data = get_user_info(user_id)
                if user_data:
                    message = (
                        f"Привет, {user_data['first_name']} {user_data['last_name']}!\n"
                        f"Твой профиль: {user_data['profile_url']}\n"
                        f"Твой город: {user_data['city']}\n"
                        f"Хочешь продолжить?"
                    )
                    keyboard = create_keyboard()
                    print("Отправка приветственного сообщения с клавиатурой...") 
                    send_message_from_group(user_id, message, user_data["attachments"], keyboard=keyboard)
            

if __name__ == '__main__':
    vk_session = vk_api.VkApi(token=GROUP_TOKEN)
    vk = vk_session.get_api()
    longpoll = VkLongPoll(vk_session)
    print("Бот запущен")
    try:
        for event in longpoll.listen():
            handle_message(event, vk)
    except Exception as e:
        print(f"Бот упал с ошибкой: {e}")
" # token_test.py Скрипт - проверка валидности токенов"
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class VK:
    def __init__(self, user_token=None, group_token=None, version='5.131'): 
        self.user_token = user_token
        self.group_token = group_token 
        self.version = version
        self.params = {'v': self.version} 

    def users_info(self, user_id, use_group_token=False): 
        """Получает информацию о пользователе, используя токен пользователя или сообщества."""
        url = 'https://api.vk.com/method/users.get'
        
        if use_group_token and self.group_token: 
            params = {'user_ids': user_id, 'access_token': self.group_token, **self.params} 
        elif self.user_token:  
             params = {'user_ids': user_id, 'access_token': self.user_token, **self.params} 
        else:
             print("Ошибка: Не предоставлен токен пользователя или токен сообщества")
             return None
        
        response = requests.get(url, params=params)
        return response.json()


# Получаем токен и ID пользователя из переменных окружения
user_access_token = os.getenv('VKTOKEN') 
user_id = os.getenv('VKUSER')
group_access_token = os.getenv('VKTOKENGROUP') 

# Создаем экземпляр класса VK, передавая токены
vk = VK(user_token=user_access_token, group_token=group_access_token) 

# Вызываем метод users_info с токеном пользователя и выводим результат
print("Информация о пользователе с токеном пользователя:")
user_info_with_user_token = vk.users_info(user_id)
if user_info_with_user_token: 
     print(user_info_with_user_token)

# Вызываем метод users_info с токеном сообщества и выводим результат
print("\nИнформация о пользователе с токеном сообщества:")
user_info_with_group_token = vk.users_info(user_id, use_group_token=True)
if user_info_with_group_token: 
    print(user_info_with_group_token)
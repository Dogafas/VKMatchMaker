import requests
import os

class VK:
    def __init__(self, access_token, user_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}
    
    def users_info(self):
      url = 'https://api.vk.com/method/users.get'
      params = {'user_ids': self.id, **self.params}
      response = requests.get(url, params=params)
      return response.json()

access_token = os.getenv('VKTOKEN') # токен полученный из инструкции
user_id = os.getenv('VKUSER') # идентификатор пользователя vk
vk = VK(access_token, user_id)
print(vk.users_info())
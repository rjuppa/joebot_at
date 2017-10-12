import json
import requests
from django.conf import settings

URL = "https://api.telegram.org/bot{}/"


class MessageBot(object):

    def __init__(self):
        self.TELEGRAM_URL = settings.TELEGRAM_URL
        self.TELEGRAM_CHAT_ID = settings.TELEGRAM_CHAT_ID

    def get_url(self, url):
        response = requests.get(url)
        content = response.content.decode("utf8")
        return content

    def get_json_from_url(self, url):
        content = self.get_url(url)
        js = json.loads(content)
        return js

    def get_updates(self):
        url = self.TELEGRAM_URL + "getUpdates"
        js = self.get_json_from_url(url)
        return js

    def get_last_chat_id_and_text(self):
        updates = self.get_updates()
        num_updates = len(updates["result"])
        last_update = num_updates - 1
        text = updates["result"][last_update]["message"]["text"]
        chat_id = updates["result"][last_update]["message"]["chat"]["id"]
        return text, chat_id

    def send_message(self, text, chat_id):
        url = self.TELEGRAM_URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
        self.get_url(url)

    def send_message_to_me(self, text):
        self.send_message(text, self.TELEGRAM_CHAT_ID)

    def process_messages(self):
        text, chat = self.get_last_chat_id_and_text()
        if text:
            text = '{} - accepted.'.format(text)
            self.send_message(text, chat)

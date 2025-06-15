import json
import os

class Messages:
    FILE = "data/messages.json"
    _messages = {}

    @classmethod
    def load(cls):
        if os.path.exists(cls.FILE):
            try:
                with open(cls.FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        cls._messages = {}
                    else:
                        cls._messages = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[Ошибка загрузки сообщений] {e}")
                cls._messages = {}
        else:
            cls._messages = {}

    @classmethod
    def save(cls):
        with open(cls.FILE, 'w', encoding='utf-8') as f:
            json.dump(cls._messages, f, ensure_ascii=False, indent=4)

    @classmethod
    def get(cls, key):
        return cls._messages.get(key, f"[Сообщение {key} не найдено]")

    @classmethod
    def set(cls, key, value):
        cls._messages[key] = value
        cls.save()


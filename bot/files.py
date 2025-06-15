import json
import os

class Files:
    FILE = "data/files.json"
    _files = {}
    FILES_DIR = "assets"

    @classmethod
    def load(cls):
        if os.path.exists(cls.FILE):
            try:
                with open(cls.FILE, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        cls._files = {}
                    else:
                        cls._files = json.loads(content)
            except json.JSONDecodeError as e:
                print(f"[Ошибка загрузки сообщений] {e}")
                cls._files = {}
        else:
            cls._files = {}

    @classmethod
    def save(cls):
        with open(cls.FILE, 'w', encoding='utf-8') as f:
            json.dump(cls._files, f)

    @classmethod
    def get(cls, key):
        return cls._files.get(key, f"[Вложение {key} не найдено]")

    @classmethod
    def set(cls, key, value):
        cls._files[key] = value
        cls.save()
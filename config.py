import json
import os


class Config:
    VK_TOKEN = "vk1.a.J62NmHgPn4nZoBR0wi8SYkS5l0CQnc3Op7D-yQB7PQuJ3kQD4DmIVCO4ZBiAU1eYGd0EUx6I-rY5EjTdhBtSTIwLTl5pDIBAXZ_COGFMP9AiuQqL34nhUP09rQj8208rsHfGe3eSuCU5s7cPHbKw0efy24XSspIIVhP7_PBL1vMGYrwCCjFcp5c11tef52-2uPOqPK3kQ9zyBdz3msLZtw"
    GROUP_ID = 181101763
    EXCEL_PATH = "assets/Spisok.xlsx"
    ADMINS = []
    IMMUTABLE_ADMINS = [82522897]
    SETTINGS_FILE = "data/settings.json"

    @classmethod
    def load_settings(cls):
        if not os.path.exists(cls.SETTINGS_FILE):
            cls.ADMINS = []
            cls.save_settings()
            return

        try:
            with open(cls.SETTINGS_FILE, 'r', encoding='utf-8') as file:
                settings = json.load(file)
                cls.ADMINS = settings.get("admins", [])
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Ошибка чтения файла настроек: {e}. Создание нового файл.")
            cls.ADMINS = []
            cls.save_settings()

    @classmethod
    def save_settings(cls):
        settings = {"admins": cls.ADMINS}
        with open(cls.SETTINGS_FILE, 'w', encoding='utf-8') as file:
            json.dump(settings, file, ensure_ascii=False, indent=4)


Config.load_settings()
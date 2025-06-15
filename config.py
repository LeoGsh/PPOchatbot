import json
import os


class Config:
    VK_TOKEN = "vk1.a.Z8X782jtS0kHBm3FHlmb5I9q7EwqyVVtzgFm9q8yRMtdQbvFbttV0_1jOTbcMjtyqAEwWSR9RMIA1Fi1qo_JoFyu5B47Fk017b-KTL16h74RDB2TuJI0W9AgixQK1qMqzqBmeUZvuHoQ5S1POOhvcZizVmeZvaUCXb14YlaZ7PbhQYkvJymqpO4eH2YUMP33b7y9QCP0pe076lDrCHjLRg"
    GROUP_ID = 491911
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
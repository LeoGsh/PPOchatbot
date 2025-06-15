import pandas as pd
from config import Config
class Database:
    def __init__(self, excel_path=Config.EXCEL_PATH):
        try:
            self.df = pd.read_excel(excel_path)
            self.df.columns = self.df.columns.str.strip()
        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке базы данных: {e}")

    def find_user_by_fio(self, fio_query):
        try:
            matches = self.df[self.df['ФИО'].str.strip().str.lower() == fio_query.lower()]
            if not matches.empty:
                return matches.iloc[0].to_dict()
            return None
        except Exception as e:
            print(f"[ERROR] Ошибка при поиске пользователя find_user_by_fio: {e}")
            return None

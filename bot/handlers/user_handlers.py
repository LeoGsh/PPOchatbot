import os

from vk_api import VkUpload

from bot.keyboards import Keyboards
import config
import vk_api

from bot.utils.doc_generator import generate_document


def process_fio_input(self, user_id, text):
    try:

        parts = text.strip().split()
        if len(parts) != 3:
            self.send_message(
                user_id,
                "Пожалуйста, введите ФИО в формате: Фамилия Имя Отчество",
                keyboard=Keyboards.create_standart_menu())
            return False

        user_data = self.database.find_user_by_fio(text.strip())

        if not user_data:
            self.send_message(
                user_id,
                "ФИО не найдено. Попробуйте ввести ФИО снова или вернитесь в главное меню",
                keyboard=Keyboards.create_standart_menu())
            return False

        self.state_manager.set_state(
            user_id,
            step="waiting_confirm",
            fio=user_data["ФИО"].strip(),
            birth=user_data["Дата рождения"],
            epb=user_data["Номер ЭПБ"]
        )

        self.send_message(
            user_id,
            f"Найдено:\n"
            f"ФИО: {user_data['ФИО']}\n"
            f"Дата рождения: {user_data['Дата рождения']}\n"
            "Все верно?",
           keyboard= Keyboards.create_yes_no_keyboard()
        )
        return True
    except Exception as e:
        print(f"[ERROR] Ошибка в process_fio_input: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")
        return None


def _handle_user_question(self, user_id, question_text):
    try:
        self.send_message(
            user_id,
            "Спасибо за ваш вопрос! Администратор ответит Вам в ближайшее время.",
            keyboard = self.keyboards.create_main_menu()
        )

        admin_ids = config.Config.ADMINS

        if not admin_ids:
            print("Нет админов для уведомления")
            return

        user_info = self.vk.users.get(user_ids=user_id, fields='first_name,last_name')[0]
        user_name = f"{user_info['first_name']} {user_info['last_name']}"


        for admin_id in admin_ids:
            try:
                self.send_message(
                    admin_id,
                    f"📨 Новый вопрос от {user_name} (https://vk.com/gim{config.Config.GROUP_ID}?sel={user_id}):\n\n{question_text}\n\n",
                    keyboard=None
                )
            except vk_api.exceptions.ApiError as e:
                print(f"Ошибка при отправке админу (id {admin_id}): {e}")

        self.state_manager.clear_state(user_id)

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_user_question: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")
        return None

FILLING_STEPS = [
    {"key": "fio", "prompt": "Шаг №1\nНапиши своё ФИО (формат: Иванов Иван Иванович)"},
    {"key": "inst", "prompt": "Шаг №2\nНапиши свой институт сокращенно (например: ИСИ, ИСиГН, ИМЭиТ и т.д.)"},
    {"key": "group", "prompt": "Шаг №3\nНапиши свою группу (пример: 5Б15 ЦИМ-11, 8СПО09ИСП-42/21, 6Б44 ППО-31 и т.д.)"},
    {"key": "phone", "prompt": "Шаг №4\nНапиши свой номер телефона"},
    {"key": "email", "prompt": "Шаг №5\nНапиши свой email"},
]

def _handle_filling_spp(self, user_id, text):
    try:
        user_data = self.state_manager.get_user_data(user_id)
        progress = user_data.get('fill_progress', 0)

        if progress > 0 and progress <= len(FILLING_STEPS):
            key = FILLING_STEPS[progress - 1]['key']
            if key == "fio" and text:
                parts = text.strip().split()
                if len(parts) == 3:
                    surname, firstname, patronymic = parts
                    user_data["fio"] = text
                    user_data["signature"] = f"{surname} {firstname[0]}. {patronymic[0]}."
                else:
                    self.send_message(user_id, "Пожалуйста, введите ФИО в формате: Фамилия Имя Отчество")
                    return
            elif text:
                user_data[key] = text

        if progress >= len(FILLING_STEPS):
            self.send_message(user_id, "Спасибо! Секундочку, заявление формируется...")

            values = {
                "fio": user_data.get("fio", ""),
                "signature": user_data.get("signature", ""),
                "inst": user_data.get("inst", ""),
                "group": user_data.get("group", ""),
                "phone": user_data.get("phone", ""),
                "email": user_data.get("email", ""),
            }

            filepath = generate_document(values)

            try:
                upload = VkUpload(self.vk_session)
                doc_upload = upload.document_message(
                    doc=filepath,
                    title="Заявление_СПП.docx",
                    peer_id=user_id
                )
                print(doc_upload)

                doc_info = doc_upload['doc']
                doc_str = f"doc{doc_info['owner_id']}_{doc_info['id']}"
                if doc_info.get('access_key'):
                    doc_str += f"_{doc_info['access_key']}"

                self.send_message(user_id, "Спасибо за ожидание! Сформированное заявление:", attachment=doc_str)
                self.send_message(
                    user_id,
                    "Чем еще могу помочь? 😊",
                    keyboard=Keyboards.create_main_menu()
                )

            except Exception as e:
                self.send_message(user_id, f"❌ Извините! Возникла ошибка при отправке документа. Попробуйте позже")
                print(f"[DEBUG]: ошибка при отправке документа {e}")

            finally:
                try:
                    os.remove(filepath)
                except Exception as e:
                    print(f"Не удалось удалить временный файл {filepath}: {e}")

            self.state_manager.clear_state(user_id)
            return

        step_info = FILLING_STEPS[progress]
        self.send_message(
            user_id,
            step_info['prompt'],
            keyboard=Keyboards.create_standart_menu())

        user_data["fill_progress"] = progress + 1

        self.state_manager.set_state(
            user_id,
            step="filling_spp",
            **user_data
        )

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_filling_spp: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

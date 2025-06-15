import json

import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from bot.handlers import admin_handlers
from bot.handlers import payload_handlers
from bot.handlers import user_handlers
from bot.keyboards import Keyboards
from bot.database import Database
from bot.states import StateManager
from bot.handlers.admin_handlers import *



class VKBot:

    def __init__(self):
        try:
            self.vk_session = vk_api.VkApi(token=config.Config.VK_TOKEN)
            self.longpoll = VkLongPoll(self.vk_session)
            self.vk = self.vk_session.get_api()

            self.keyboards = Keyboards()
            self.database = Database(excel_path=config.Config.EXCEL_PATH)
            self.state_manager = StateManager()

            self.new_users = set()

            config.Config.load_settings()
            Messages.load()
            Files.load()

            print("Бот инициализирован")

        except Exception as e:
            print(f"[ERROR] Ошибка при инициализации бота: {e}")

    def send_message(self, user_id, message, attachment=None, keyboard=None):
        try:
            if isinstance(attachment, list):
                vk_attachments = []
                for att in attachment:
                    if isinstance(att, dict):
                        vk_attachments.append(att['value'])
                    else:
                        vk_attachments.append(str(att))
                attachment = ','.join(vk_attachments)
            elif attachment and not isinstance(attachment, str):
                attachment = str(attachment)
            params = {
                'user_id': user_id,
                'message': message,
                'random_id': 0
            }

            if attachment:
                params['attachment'] = attachment
            if keyboard:
                params['keyboard'] = keyboard
            self.vk.messages.send(**params)
        except Exception as e:
            print(f"Ошибка отправки сообщения: {e}")
            try:
                self.vk.messages.send(
                    user_id=user_id,
                    message=f"{message}\n\n⚠ Не удалось отправить вложение",
                    random_id=0
                )
            except Exception as e:
                print(f"Ошибка отправки сообщения: {e}")

    def handle_new_user(self, user_id):
        try:
            self.send_message(
                user_id,
                message = Messages.get("welcome"),
                attachment=Files.get("welcome"),
                keyboard = self.keyboards.create_main_menu()
            )
            self.new_users.add(user_id)
        except Exception as e:
            print(f"[ERROR] Ошибка в handle_new_user: {e}")
            self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

    def process_payload(self, user_id, payload):
        try:
            payload_data = json.loads(payload)
            action_type = payload_data.get("type")

            if action_type in payload_handlers.template_handlers:
                key, keyboard = payload_handlers.template_handlers[action_type]
                payload_handlers.handle_template(self, user_id, key, keyboard)
                return True

            if action_type == "get_epb":
                self.state_manager.set_state(user_id, step="waiting_fio")
                self.send_message(
                    user_id,
                    "Пожалуйста, введите ваше ФИО (формат: Иванов Иван Иванович)",
                    keyboard = Keyboards.create_standart_menu())

                return True

            if action_type == "another_question":
                self.state_manager.set_state(user_id, step="waiting_question")
                self.send_message(user_id, "Пожалуйста, напишите ваш вопрос:")
                return True

            if action_type == "fill":
                self.send_message(
                    user_id,
                    "Отлично! Тогда начнем заполнять заявление.\n\n"
                    "Ответь на 5 моих вопросов и я пришлю тебе заполненное заявление!\n\n"
                )
                self.state_manager.set_state(user_id, step="filling_spp")
                user_handlers._handle_filling_spp(self, user_id, None)

                return True

            if action_type == "main_menu":
                self.state_manager.clear_state(user_id)
                self.send_message(
                    user_id,
                    "Возвращаю в главное меню:",
                    keyboard = self.keyboards.create_main_menu()
                )
                return True

        except json.JSONDecodeError:
            self.send_message(user_id, "Ошибка обработки действия")
        return False

    def process_message(self, event):
        try:
            user_id = event.user_id
            text = event.text if hasattr(event, 'text') else ""

            step = self.state_manager.get_step(user_id)

            if hasattr(event, 'payload') and event.payload:
                if self.process_payload(user_id, event.payload):
                    return

            is_exited = self.state_manager.get_step("admin_mode_exited")

            if user_id in config.Config.ADMINS and not is_exited:
                is_exited = self.state_manager.get_user_data(user_id).get("admin_mode_exited", False)
                if not is_exited:
                    admin_handlers._handle_admin_command(self, user_id, text, event)
                    return

            if user_id not in self.new_users:
                self.handle_new_user(user_id)
                return

            if step == "waiting_fio":
                user_handlers.process_fio_input(self, user_id, text)
                return

            if step == "waiting_confirm":
                payload_handlers.process_confirmation(self, user_id, text)
                return

            if step == "waiting_question":
                user_handlers._handle_user_question(self, user_id, text)

            if step == "filling_spp":
                user_handlers._handle_filling_spp(self, user_id, text)
                return


            elif text.startswith("/"):
                if user_id in config.Config.ADMINS:
                    admin_handlers._handle_admin_command(self, user_id, text, event)
                else:
                    self.send_message(
                        user_id,
                        "Пожалуйста, выберите действие",
                        keyboard = self.keyboards.create_main_menu()
                    )

            elif text == "пока":
                self.send_message(user_id, "До встречи! 👋")

            else:
                self.send_message(
                    user_id,
                    "Выберите действие:",
                    keyboard = self.keyboards.create_main_menu()
                )
        except Exception as e:
            print(f"[ERROR] Ошибка в process_message: {e}")

    def run(self):
        print("Бот читает")
        while True:
            try:
                self.longpoll = VkLongPoll(self.vk_session)
                for event in self.longpoll.listen():
                    if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                        self.process_message(event)
            except Exception as e:
                print(f"[ERROR] Ошибка в run: {e}")
                time.sleep(5)
import os
import time

import config
import requests
from vk_api import VkUpload

from bot.files import Files
from bot.messages import Messages
from bot.utils import admin_utils


def _handle_waiting_confirmation(self, user_id, text):
    try:
        user_data = self.state_manager.get_user_data(user_id)
        key = user_data.get("key")
        new_text = user_data.get("new_text")

        if text.strip().lower() == "да":
            import html
            decoded_text = html.unescape(new_text)
            Messages.set(key, decoded_text)
            self.send_message(user_id, f"✅ Текст для '{key}' обновлён.")
        else:
            self.send_message(user_id, "❌ Изменение отменено.")

        self.state_manager.clear_state(user_id)
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_waiting_confirmation: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_waiting_text(self, user_id, text, event):
    try:
        key = self.state_manager.get_user_data(user_id).get("key")
        self.state_manager.set_state(user_id, "waiting_confirmation", key=key, new_text=text)
        self.send_message(
            user_id,
            f"Новый текст для /{key}:\n\n{text}\n\nВы уверены, что хотите сохранить?\n- да\n- нет"
        )
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_waiting_text: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_admin_command(self, user_id, text, event):
    try:
        step = self.state_manager.get_step(user_id)

        if step == "waiting_new_file":
            _handle_waiting_file(self, user_id, event)
            return
        if step == "waiting_new_text":
            _handle_waiting_text(self, user_id, text, event)
            return
        if step == "editing_file_mode":
            _handle_editing_file_mode(self, user_id, text)
            return
        if step == "editing_mode":
            _handle_editing_mode(self, user_id, text)
            return
        if step == "waiting_confirmation":
            _handle_waiting_confirmation(self, user_id, text)
            return

        parts = text.strip().split()

        if not parts:
            self.send_message(user_id, "Перед отправкой файла, пожалуйста, введите необходимую команду.")
            _handle_admin_help(self, user_id)
            return

        command = parts[0]
        args = parts[1:]

        command_handlers = {
            "/show_admins": _handle_show_admins,
            "/add_admin": _handle_add_admin,
            "/delete_admin": _handle_delete_admin,
            "/edit_spis": _handle_edit_spis,
            "/edit_text": _handle_edit_text,
            "/edit_file": _handle_edit_file,
            "/admin": _handle_admin_help,
            "/exit": _handle_exit_admin_mode
        }

        handler = command_handlers.get(command)
        if handler is not None:
            handler(self, user_id, args, event)
        else:
            self.send_message(user_id, "Неизвестная админ-команда.")
            _handle_admin_help(self, user_id)

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_admin_command: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_exit_admin_mode(self, user_id, args, event):
    try:

        current_step = self.state_manager.get_step(user_id)
        self.state_manager.set_state(user_id, current_step, admin_mode_exited=True)
        self.send_message(
            user_id,
            "Вы временно вышли из админ-режима.\n"
            "Теперь бот обрабатывает вас как обычного пользователя.\n\n"
            "Чтобы вернуться в админ-панель, введите /admin"
        )
        self.handle_new_user(user_id)

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_exit_admin_mode: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")


def _handle_admin_help(self, user_id, args=None, event=None):
    try:

        if self.state_manager.get_step("admin_mode_exited"):
            self.state_manager.clear_state(user_id, "admin_mode_exited")
        self.send_message(
            user_id,
            "💡 Админ панель. Список команд:\n\n"
            "/admin - показать список команд\n"
            "/show_admins - показать список админов\n"
            "/add_admin - добавить админа\n"
            "/delete_admin - удалить админа\n"
            "/edit_text - редактировать текст сообщений бота\n"
            "/edit_file - редактировать файлы сообщений бота\n"
            "/edit_spis - редактировать базу данных ЭПБ\n"
            "/exit - выход из админ режима\n"

        )
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_admin_help: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_show_admins(self, user_id, args, event):
    try:
        admins = config.Config.ADMINS
        if not admins:
            self.send_message(user_id, "Список админов пуст.")
        else:
            admin_list = "\n".join([f"vk.com/id{aid}" for aid in admins])
            self.send_message(user_id, f"Список админов:\n{admin_list}")
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_show_admins: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_add_admin(self, user_id, args, event):
    try:
        if len(args) != 1:
            self.send_message(
                user_id,
                "⚠️ Формат: /add_admin <ID или Никнейм>\n"
                "Например: /add_admin leo_gsh")
            return

        arg = args[0]
        new_admin = int(arg) if arg.isdigit() else admin_utils.get_user_id_by_nickname(self, arg)

        if new_admin is None:
            self.send_message(user_id, f"❌ Не удалось найти пользователя с никнеймом {arg}, или неправильный ID.")
            return

        if new_admin in config.Config.ADMINS:
            self.send_message(user_id, f"vk.com/id{new_admin} уже админ.")
        else:
            config.Config.ADMINS.append(new_admin)
            config.Config.save_settings()
            self.send_message(user_id, f"✅ Добавлен vk.com/id{new_admin} в список админов.")
        return
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_add_admin: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")


def _handle_delete_admin(self, user_id, args, event):
    try:
        if len(args) != 1:
            self.send_message(
                user_id,
                "⚠️ Формат: /delete_admin <ID или Никнейм>\n"
                "Например: /delete_admin leo_gsh")
            return

        arg = args[0]
        remove_id = int(arg) if arg.isdigit() else admin_utils.get_user_id_by_nickname(self, arg)

        if remove_id is None:
            self.send_message(user_id, f"❌ Не удалось найти пользователя с никнеймом {arg}, или неправильный ID.")
            return

        if remove_id in config.Config.IMMUTABLE_ADMINS:
            self.send_message(user_id, "❌ Нельзя удалить основного администратора.")
            return

        if remove_id in config.Config.ADMINS:
            config.Config.ADMINS.remove(remove_id)
            config.Config.save_settings()
            self.send_message(user_id, f"✅ Удалён vk.com/id{remove_id} из списка админов.")
        else:
            self.send_message(user_id, "❌ Такого админа нет.")
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_delete_admin: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_edit_spis(self, user_id, args, event):
    try:
        full_event = self.vk.messages.getById(message_ids=event.message_id)['items'][0]
        attachments = full_event.get("attachments")

        if not attachments:
            self.send_message(user_id, "⚠️Формат: /edit_spis с прикреплённым Excel-файлом (.xlsx)")
            return

        attachment = attachments[0]
        if attachment.get("type") != "doc":
            self.send_message(user_id, "Пожалуйста, введите команду /edit_spis и прикрепите Excel-файл с базой данных (.xlsx)")
            return

        doc = attachment["doc"]
        doc_url = doc.get('url')

        try:
            response = requests.get(doc_url)
            response.raise_for_status()

            filename = f"assets/Spisok.xlsx"
            with open(filename, "wb") as f:
                f.write(response.content)

            print(f"[INFO] Документ сохранён: {filename}")
            self.send_message(user_id, "✅ Обновление нового списка с номерами ЭПБ успешно. Данные обновлены.")

        except Exception as e:
            print(f"[ERROR] Ошибка при загрузке документа: {e}")
            self.send_message(user_id, "❌ Произошла ошибка при загрузке документа.")

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_edit_spis: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")


def _handle_edit_text(self, user_id, args, event):
    try:
        Messages.load()
        response = "Введите ключ, сообщение которого вы хотите изменить:\n\n"
        for key in Messages._messages:
            preview = Messages._messages[key].split("\n")[0]
            response += f"/{key} — {preview}...\n"

        self.send_message(user_id, response)
        self.state_manager.set_state(user_id, "editing_mode")

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_edit_text: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_editing_mode(self, user_id, text):
    try:
        if text == "/admin":
            self.state_manager.clear_state(user_id)
            _handle_admin_help(self, user_id)
            return

        if not Messages._messages:
            self.send_message(user_id, "❌ Нет доступных сообщений.")
            return

        if not text.startswith("/"):
            self.send_message(
                user_id,
                "⚠️ Введите команду в формате /ключ_сообщения\n"
                "Или введите /admin для выхода из режима редактирования")
            return

        key = text[1:]
        if key not in Messages._messages:
            self.send_message(
                user_id,
                f"❌ Сообщение с ключом /{key} не найдено.\n"
                f"Введите правильный ключ или /admin для выхода из режима редактирования")
            return

        self.state_manager.set_state(user_id, "waiting_new_text", key=key)
        current_message = Messages.get(key)
        self.send_message(
            user_id,
            f"Текущий текст для сообщения /{key}:\n\n{current_message}")
        self.send_message(user_id, f"Введите новый текст для сообщения /{key}:")

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_editing_mode: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_edit_file(self, user_id, args, event):
    try:
        Files.load()
        response = "Введите ключ сообщения, файлы которого хотите изменить:\n\n"
        for key in Files._files:
            response += f"/{key}\n"

        self.send_message(user_id, response)
        self.state_manager.set_state(user_id, "editing_file_mode")
    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_edit_file: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_editing_file_mode(self, user_id, text):
    try:
        if text == "/admin":
            self.state_manager.clear_state(user_id)
            _handle_admin_help(self, user_id)
            return

        if not Files._files:
            self.send_message(user_id, "❌ Нет доступных сообщений.")
            return

        if not text.startswith("/"):
            self.send_message(
                user_id,
                "⚠️ Введите команду в формате /ключ_сообщения\n"
                "Или введите /admin для выхода из режима редактирования")
            return

        key = text[1:]
        if key not in Files._files:
            self.send_message(
                user_id,
                f"❌ Сообщение с ключом /{key} не найдено.\n"
                f"Введите правильный ключ или /admin для выхода из режима редактирования")
            return

        self.state_manager.set_state(user_id, "waiting_new_file", key=key)
        current_files = Files.get(key)

        if not current_files or len(current_files) == 0:
            self.send_message(user_id, f"Для сообщения /{key} нет файлов.")
        else:
            self.send_message(
                user_id,
                f"Текущие файлы для сообщения /{key}",
                attachment=current_files
            )

        self.send_message(user_id, f"Отправьте новый файл для сообщения /{key}:")

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_editing_file_mode: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

def _handle_waiting_file(self, user_id, event):
    try:
        key = self.state_manager.get_user_data(user_id).get("key")
        try:
            full_event = self.vk.messages.getById(message_ids=event.message_id)['items'][0]
        except Exception as e:
            print(f"[ERROR] Не удалось получить сообщение по ID: {e}")
            self.send_message(user_id, "❌ Ошибка получения данных сообщения.")
            return

        attachments = full_event.get("attachments", [])
        print(f"[DEBUG] Получены вложения: {attachments}")

        attachments_list = []

        for idx, attachment in enumerate(attachments):
            if attachment.get("type") == "photo":
                photo = attachment["photo"]
                print(f"[DEBUG] Найдено фото: {photo}")

                try:
                    sizes = photo.get("sizes", [])
                    if not sizes:
                        print("[WARNING] У фото нет sizes")
                        continue
                    largest = sorted(sizes, key=lambda x: x["width"] * x["height"])[-1]
                    photo_url = largest["url"]
                    print(f"[DEBUG] URL изображения: {photo_url}")

                    response = requests.get(photo_url)
                    response.raise_for_status()

                    file_extension = photo_url.split('.')[-1].split('?')[0]
                    filename = f"assets/{key}_photo_{int(time.time())}_{idx}.{file_extension}"

                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"[INFO] Фото сохранено: {filename}")

                    upload = VkUpload(self.vk_session)
                    attachment_info = upload.photo_messages(filename)
                    photo_info = attachment_info[0]
                    owner_id = photo_info['owner_id']
                    photo_id = photo_info['id']
                    access_key = photo_info.get('access_key')

                    attachment_str = f"photo{owner_id}_{photo_id}"
                    if access_key:
                        attachment_str += f"_{access_key}"

                    attachments_list.append({
                        "type": "photo",
                        "value": attachment_str,
                        "filename": filename
                    })

                    try:
                        os.remove(filename)
                        print(f"[INFO] Файл {filename} удален с сервера")
                    except Exception as e:
                        print(f"[WARNING] Не удалось удалить файл {filename}: {e}")

                except Exception as e:
                    print(f"[ERROR] Ошибка обработки фото: {e}")
                    self.send_message(user_id, "❌ Не удалось обработать фото.")

            elif attachment.get("type") == "doc":
                doc = attachment["doc"]
                print(f"[DEBUG] Найден документ: {doc}")

                try:
                    allowed_ext = ['doc', 'docx', 'pdf', 'xls', 'xlsx', 'txt']
                    ext = doc.get('ext')

                    if ext not in allowed_ext:
                        print(f"[WARNING] Неподдерживаемый тип документа: {ext}")
                        self.send_message(user_id, f"❌ Тип документа .{ext} не поддерживается.")
                        continue

                    doc_url = doc.get('url')
                    if not doc_url:
                        print("[WARNING] У документа нет URL")
                        continue

                    response = requests.get(doc_url)
                    response.raise_for_status()

                    filename = f"assets/{key}_doc_{int(time.time())}_{idx}.{ext}"

                    with open(filename, "wb") as f:
                        f.write(response.content)
                    print(f"[INFO] Документ сохранён: {filename}")

                    upload = VkUpload(self.vk_session)

                    doc_upload = upload.document_message(
                        doc=filename,
                        title=doc.get('title', f"document_{key}"),
                        peer_id=event.peer_id
                    )

                    doc_info = doc_upload['doc']
                    doc_str = f"doc{doc_info['owner_id']}_{doc_info['id']}"
                    if doc_info.get('access_key'):
                        doc_str += f"_{doc_info['access_key']}"

                    attachments_list.append({
                        "type": "doc",
                        "value": doc_str,
                        "filename": filename,
                        "ext": ext,
                        "title": doc.get('title', '')
                    })

                    try:
                        os.remove(filename)
                        print(f"[INFO] Файл {filename} удален с сервера")
                    except Exception as e:
                        print(f"[WARNING] Не удалось удалить файл {filename}: {e}")

                except Exception as e:
                    print(f"[ERROR] Ошибка обработки документа: {e}")
                    self.send_message(user_id, "❌ Не удалось обработать документ.")

        if attachments_list:
            try:
                Files.load()
                Files._files[key] = attachments_list
                Files.save()

                print(f"[DEBUG] Сохранено в JSON для ключа '{key}': {attachments_list}")

                photo_count = sum(1 for item in attachments_list if item["type"] == "photo")
                doc_count = sum(1 for item in attachments_list if item["type"] == "doc")

                msg = f"✅ Для ключа /{key} успешно сохранено:\n"
                if photo_count > 0:
                    msg += f"📷 Фото: {photo_count} шт.\n"
                if doc_count > 0:
                    msg += f"📄 Документов: {doc_count} шт."

                self.send_message(user_id, msg)

            except Exception as e:
                print(f"[CRITICAL] Ошибка сохранения JSON: {e}")
                self.send_message(user_id, "❌ Критическая ошибка при сохранении данных.")

        self.state_manager.clear_state(user_id)

    except Exception as e:
        print(f"[ERROR] Ошибка в _handle_waiting_file: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")


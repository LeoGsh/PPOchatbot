from bot.files import Files
from bot.messages import Messages
from bot.keyboards import Keyboards


def process_confirmation(self, user_id, text):
    try:
        if text.lower() == "да":
            data = self.state_manager.get_user_data(user_id)
            self.send_message(user_id, f"Ваш номер электронного профсоюзного билета (ЭПБ): "
                                       f"\n{data['epb']}")
            self.send_message(
                user_id,
                Messages.get("epb_info")
            )
            self.state_manager.clear_state(user_id)

            self.send_message(
                user_id,
                "Чем еще могу помочь? 😊",
                keyboard = Keyboards.create_main_menu()
            )
        elif text.lower() == "нет":
            self.send_message(
                user_id,
                "Попробуйте ввести ФИО снова или вернитесь в главное меню",
                keyboard=Keyboards.create_standart_menu())
            self.state_manager.set_state(user_id, step="waiting_fio")
        else:
            self.send_message(
                user_id,
                "Пожалуйста, выберите Да или Нет",
                keyboard=Keyboards.create_yes_no_keyboard())

    except Exception as e:
        print(f"[ERROR] Ошибка в process_confirmation: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

template_handlers = {
    "question_SPP": ("spp_info", Keyboards.create_spp_menu),
    "how_spp": ("how_spp", Keyboards.create_filling_menu),
    "question_MP": ("mp_info", Keyboards.create_mp_menu),
    "confirm_vsu": ("mp_vsu_info", Keyboards.create_standart_menu),
    "confirm_prof": ("mp_prof_info", Keyboards.create_standart_menu),
    "question_PGAS": ("pgas_info", Keyboards.create_pgas_menu),
    "how_pgas": ("how_pgas", Keyboards.create_standart_menu),
    "join_prof": ("join_prof", Keyboards.create_standart_menu),
    "more_prof": ("info_prof", Keyboards.create_standart_menu),
}

def handle_template(self, user_id, key, keyboard_func):
    try:
        self.send_message(
            user_id,
            Messages.get(key),
            Files.get(key),
            keyboard=keyboard_func()
        )
    except Exception as e:
        print(f"Ошибка при обработке {key}: {e}")
        self.send_message(user_id, "Извините, произошла внутренняя ошибка. Попробуйте повторить действие позже")

import json
from vk_api.keyboard import VkKeyboard, VkKeyboardColor

def btn(label, color, payload_type):
    return {
        "label": label,
        "color": color,
        "payload": json.dumps({"type": payload_type})
    }

class BaseKeyboard:
    STANDARD_BUTTON = btn("В меню", VkKeyboardColor.PRIMARY, "main_menu")
    ANOTHER_BUTTON = btn("Другой вопрос", VkKeyboardColor.SECONDARY, "another_question")

    @staticmethod
    def add_button(keyboard, button):
        keyboard.add_button(button["label"], color=button["color"], payload=button["payload"])

    @staticmethod
    def add_line(keyboard):
        keyboard.add_line()

class Keyboards:
    @staticmethod
    def _create(rows):
        keyboard = VkKeyboard(one_time=False)
        for i, row in enumerate(rows):
            for button in row:
                keyboard.add_button(**button)
            if i < len(rows) - 1:
                keyboard.add_line()
        return keyboard.get_keyboard()

    @staticmethod
    def create_main_menu():
        return Keyboards._create([
            [btn("Вопрос по Профилакторию", VkKeyboardColor.SECONDARY, "question_SPP")],
            [btn("Вопрос по мат. помощи", VkKeyboardColor.SECONDARY, "question_MP")],
            [btn("Вопрос по ПГАС", VkKeyboardColor.SECONDARY, "question_PGAS")],
            [btn("Получить номер ЭПБ", VkKeyboardColor.PRIMARY, "get_epb")],
            [
                btn("Вступить в Профсоюз", VkKeyboardColor.PRIMARY, "join_prof"),
                btn("О Профкоме", VkKeyboardColor.PRIMARY, "more_prof")
            ]
        ])

    @staticmethod
    def create_yes_no_keyboard():
        return Keyboards._create([
            [
                btn("Да", VkKeyboardColor.POSITIVE, "confirm_yes"),
                btn("Нет", VkKeyboardColor.NEGATIVE, "confirm_no")
            ],
            [BaseKeyboard.STANDARD_BUTTON]
        ])

    @staticmethod
    def create_standart_menu():
        return Keyboards._create([
            [BaseKeyboard.ANOTHER_BUTTON],
            [BaseKeyboard.STANDARD_BUTTON]
        ])

    @staticmethod
    def create_spp_menu():
        return Keyboards._create([
            [btn("Как попасть в Профилакторий?", VkKeyboardColor.SECONDARY, "how_spp")],
            [BaseKeyboard.ANOTHER_BUTTON],
            [BaseKeyboard.STANDARD_BUTTON]
        ])

    @staticmethod
    def create_filling_menu():
        return Keyboards._create([
            [btn("Хочу!", VkKeyboardColor.POSITIVE, "fill")],
            [BaseKeyboard.STANDARD_BUTTON]
        ])

    @staticmethod
    def create_mp_menu():
        return Keyboards._create([
            [
                btn("от Университета", VkKeyboardColor.SECONDARY, "confirm_vsu"),
                btn("от Профкома", VkKeyboardColor.SECONDARY, "confirm_prof")
            ]
        ])

    @staticmethod
    def create_pgas_menu():
        return Keyboards._create([
            [btn("Как получить ПГАС?", VkKeyboardColor.SECONDARY, "how_pgas")],
            [BaseKeyboard.ANOTHER_BUTTON],
            [BaseKeyboard.STANDARD_BUTTON]
        ])

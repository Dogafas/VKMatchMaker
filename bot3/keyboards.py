# keyboards.py
import json
import logging

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def create_button(label, payload, color="primary"):
    """Создает кнопку с заданными параметрами."""
    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps(payload, ensure_ascii=False),
        },
        "color": color,
    }


def create_keyboard(buttons):
    """Создает клавиатуру с заданными кнопками."""
    keyboard = {"one_time": False, "buttons": buttons}
    keyboard_json = json.dumps(keyboard, ensure_ascii=False)
    logging.info(f"Сформированная клавиатура: {keyboard_json}")
    return keyboard_json


def get_sex_keyboard():
    """Создает клавиатуру для выбора пола."""
    buttons = [
        [
            create_button("👨🏻 Мужской", {"button": "male"}, "primary"),
            create_button("👩🏻 Женский", {"button": "female"}, "primary"),
        ]
    ]
    return create_keyboard(buttons)


def get_age_keyboard():
    """Создает клавиатуру для выбора возраста."""
    buttons = [
        [
            create_button("18-25", {"button": "18-25"}, "primary"),
            create_button("26-35", {"button": "26-35"}, "primary"),
        ],
        [
            create_button("36-44", {"button": "36-44"}, "primary"),
            create_button("45+", {"button": "45+"}, "primary"),
        ],
    ]
    return create_keyboard(buttons)


def get_next_prev_keyboard():
    """Создает клавиатуру с кнопками 'Следующий' и 'Поиск'."""
    buttons = [
        [
            create_button("🔙 Предыдущий", {"button": "prev"}, "primary"),
            create_button("🔍 Поиск", {"button": "search"}, "primary"),
            
        ],
        [
            create_button("⭐ Избранное", {"button": "favorite"}, "positive"),
            create_button("🚫 Черный список", {"button": "blacklist"}, "negative"),
        ],
    ]
    return create_keyboard(buttons)


def get_yes_no_keyboard():
    """Создает клавиатуру с кнопками 'Да' и 'Нет'."""
    buttons = [
        [
            create_button("Да", {"button": "yes"}, "positive"),
            create_button("Нет", {"button": "no"}, "negative"),
        ]
    ]
    return create_keyboard(buttons)

import json
import logging 

# Настраиваем логирование
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def create_button(label, payload, color="primary"):
    """Создает кнопку с заданными параметрами."""
    return {
        "action": {
            "type": "text",
            "label": label,
            "payload": json.dumps(payload, ensure_ascii=False)
        },
        "color": color
    }

def create_keyboard(buttons):
    """Создает клавиатуру с заданными кнопками."""
    keyboard = {
        "one_time": False,
        "buttons": buttons
    }
    keyboard_json = json.dumps(keyboard, ensure_ascii=False)
    logging.info(f"Сформированная клавиатура: {keyboard_json}") 
    return keyboard_json

def get_sex_keyboard():
    """Создает клавиатуру для выбора пола."""
    buttons = [
        [
           create_button("Мужской", {"button": "male"}, "primary"),
           create_button("Женский", {"button": "female"}, "primary")
        ]
    ]
    return create_keyboard(buttons)

def get_age_keyboard():
    """Создает клавиатуру для выбора возраста."""
    buttons = [
        [
            create_button("18-25", {"button": "18-25"}, "primary"),
            create_button("25-35", {"button": "25-35"}, "primary")
        ],
        [
            create_button("35-45", {"button": "35-45"}, "primary"),
            create_button("45+", {"button": "45+"}, "primary")

        ]
    ]
    return create_keyboard(buttons)

def get_next_keyboard():
    """Создает клавиатуру с кнопкой 'Следующий'"""
    buttons = [
        [
            create_button("Следующий", {"button": "next"}, "primary")
        ]
    ]
    return create_keyboard(buttons)
def get_yes_no_keyboard():
        buttons = [
           [
               create_button("Да", {"button": "yes"}, "positive"),
               create_button("Нет", {"button": "no"}, "negative")
                ]
            ]
        return create_keyboard(buttons)
import json
import os

from utils.resource_path import resource_path


class SettingsService:

    # Папка приложения в AppData
    APP_DIR = os.path.join(
        os.environ["APPDATA"],
        "Vertical"
    )

    # Создание папки при отсутствии
    os.makedirs(APP_DIR, exist_ok=True)

    # Путь к файлу настроек
    SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")

    def __init__(self):

        # Настройки по умолчанию
        self.settings = {
            "theme": "light",
            "accuracy": 0.6,
            "language": "ru",
            "show_skeleton": True,
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5,
            "remember_user": False,
            "user_id": None
        }

        # Загрузка сохранённых настроек
        self.load_settings()

    # Загрузка настроек из JSON
    def load_settings(self):

        try:
            if os.path.exists(self.SETTINGS_FILE):

                with open(
                    self.SETTINGS_FILE,
                    "r",
                    encoding="utf-8"
                ) as f:

                    saved = json.load(f)

                    # Обновление настроек
                    self.settings.update(saved)

        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    # Сохранение настроек в JSON
    def save_settings(self):

        try:
            with open(
                self.SETTINGS_FILE,
                "w",
                encoding="utf-8"
            ) as f:

                json.dump(
                    self.settings,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    #ТЕМЫ
    # Получение текущей темы
    def get_theme(self):
        return self.settings.get("theme", "light")

    # Установка темы приложения
    def set_theme(self, theme):

        self.settings["theme"] = theme

        self.save_settings()

    #ЯЗЫК
    # Получение текущего языка
    def get_language(self):
        return self.settings.get("language", "ru")

    # Установка языка интерфейса
    def set_language(self, language):

        self.settings["language"] = language

        self.save_settings()

    #ТОЧНОСТЬ
    # Получение уровня точности
    # def get_accuracy(self):
    #     return self.settings.get("accuracy", 0.6)

    # # Изменение уровня точности анализа
    # def set_accuracy(self, accuracy):

    #     self.settings["accuracy"] = accuracy

    #     # Высокая точность
    #     if accuracy >= 0.8:

    #         self.settings["min_detection_confidence"] = 0.8
    #         self.settings["min_tracking_confidence"] = 0.7

    #     # Средняя точность
    #     elif accuracy >= 0.6:

    #         self.settings["min_detection_confidence"] = 0.5
    #         self.settings["min_tracking_confidence"] = 0.5

    #     # Низкая точность
    #     else:

    #         self.settings["min_detection_confidence"] = 0.3
    #         self.settings["min_tracking_confidence"] = 0.3

    #     self.save_settings()

    # # Конфигурация MediaPipe
    # def get_posture_config(self):

    #     return {
    #         "model_complexity": 1,

    #         "min_detection_confidence":
    #             self.settings["min_detection_confidence"],

    #         "min_tracking_confidence":
    #             self.settings["min_tracking_confidence"]
    #     }

    # Проверка отображения скелета
    def get_show_skeleton(self):
        return self.settings.get("show_skeleton", True)

    # Включение/выключение скелета
    def set_show_skeleton(self, value):

        self.settings["show_skeleton"] = value

        self.save_settings()

    #СЕССИЯ
    # Сохранение пользовательской сессии
    def save_user_session(self, user_id, remember=False):

        self.settings["user_id"] = user_id
        self.settings["remember_user"] = remember

        self.save_settings()

    # Очистка пользовательской сессии
    def clear_user_session(self):

        self.settings["remember_user"] = False
        self.settings["user_id"] = None

        self.save_settings()

    # Получение сохранённого пользователя
    def get_saved_user(self):

        if self.settings.get("remember_user") is True:
            return self.settings.get("user_id")

        return None
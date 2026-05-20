import json
import os

from utils.resource_path import resource_path


class SettingsService:
    SETTINGS_FILE = resource_path("settings.json")

    def __init__(self):
        self.settings = {
            "theme": "light",
            "accuracy": 0.6,
            "language": "ru",
            "show_skeleton": True,
            "min_detection_confidence": 0.5,
            "min_tracking_confidence": 0.5
        }

        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.SETTINGS_FILE):
                with open(self.SETTINGS_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    self.settings.update(saved)

        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")

    def save_settings(self):
        try:
            with open(self.SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(
                    self.settings,
                    f,
                    indent=4,
                    ensure_ascii=False
                )

        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

    # ===== THEME =====

    def get_theme(self):
        return self.settings.get("theme", "light")

    def set_theme(self, theme):
        self.settings["theme"] = theme
        self.save_settings()

    # ===== LANGUAGE =====

    def get_language(self):
        return self.settings.get("language", "ru")

    def set_language(self, language):
        self.settings["language"] = language
        self.save_settings()

    # ===== ACCURACY =====

    def get_accuracy(self):
        return self.settings.get("accuracy", 0.6)

    def set_accuracy(self, accuracy):
        self.settings["accuracy"] = accuracy

        if accuracy >= 0.8:
            self.settings["min_detection_confidence"] = 0.8
            self.settings["min_tracking_confidence"] = 0.7

        elif accuracy >= 0.6:
            self.settings["min_detection_confidence"] = 0.5
            self.settings["min_tracking_confidence"] = 0.5

        else:
            self.settings["min_detection_confidence"] = 0.3
            self.settings["min_tracking_confidence"] = 0.3

        self.save_settings()

    def get_posture_config(self):
        return {
            "model_complexity": 1,
            "min_detection_confidence":
                self.settings["min_detection_confidence"],

            "min_tracking_confidence":
                self.settings["min_tracking_confidence"]
        }
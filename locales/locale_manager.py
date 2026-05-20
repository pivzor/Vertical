import json
import os
from PyQt5.QtCore import QObject, pyqtSignal, QTimer
from utils.resource_path import resource_path

class LocaleManager(QObject):
    """Менеджер локализации"""

    language_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.current_language = "ru"
        self.strings = {}
        self._update_timer = None
        self.load_language(self.current_language)

    def load_language(self, lang_code):
        """Загрузка файла перевода"""
        lang_file = resource_path(f"locales/{lang_code}.json")

        try:
            with open(lang_file, "r", encoding="utf-8") as f:
                self.strings = json.load(f)
                self.current_language = lang_code
                return True
        except Exception as e:
            print(f"Error loading language {lang_code}: {e}")
            return False

    def tr(self, key, *args):
        """Получение перевода по ключу с подстановкой аргументов"""
        text = self.strings.get(key, key)
        if args:
            try:
                return text.format(*args)
            except:
                return text
        return text

    def get_language(self):
        return self.current_language

    def set_language(self, lang_code):
        if self.load_language(lang_code):
            # Используем QTimer для отсрочки сигнала, чтобы избежать задержек
            if self._update_timer:
                self._update_timer.stop()
            self._update_timer = QTimer()
            self._update_timer.setSingleShot(True)
            self._update_timer.timeout.connect(self._emit_language_changed)
            self._update_timer.start(50)
            return True
        return False

    def _emit_language_changed(self):
        self.language_changed.emit()

    def get_available_languages(self):
        return [
            {"code": "ru", "name": self.tr("language_russian")},
            {"code": "en", "name": self.tr("language_english")}
        ]


# Глобальный экземпляр менеджера локализации
_locale = None


def get_locale():
    global _locale
    if _locale is None:
        _locale = LocaleManager()
    return _locale


def tr(key, *args):
    return get_locale().tr(key, *args)
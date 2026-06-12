import sys
import os

# Включение корректного масштабирования интерфейса
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "1"
os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
os.environ["QT_SCALE_FACTOR_ROUNDING_POLICY"] = "PassThrough"

import traceback

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

# Настройки High DPI для Qt
QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

from auth.login_window import LoginWindow
from ui.main_window import MainWindow
from services.settings_service import SettingsService
from locales.locale_manager import get_locale
from utils.resource_path import resource_path

# Отключение лишних логов TensorFlow
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


if __name__ == "__main__":

    print("APP STARTED")

    import ctypes

    myappid = "vertical"
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)

    try:
        # Создание Qt-приложения
        app = QApplication(sys.argv)

        print("QApplication created")

        # Сервис настроек приложения
        settings_service = SettingsService()

        # Получение текущей темы
        theme = settings_service.get_theme()

        # Выбор файла стилей
        styles_path = (
            resource_path("styles/style_dark.qss")
            if theme == "dark"
            else resource_path("styles/style_light.qss")
        )

        # Загрузка QSS-стилей
        with open(styles_path, "r", encoding="utf-8") as f:
            app.setStyleSheet(f.read())

        # Настройка базового шрифта
        font = app.font()
        font.setPointSize(11)
        app.setFont(font)

        # Установка иконки приложения
        try:
            app.setWindowIcon(
                QIcon(resource_path("assets/img/icon.ico"))
            )

        except Exception as e:
            print("Icon error:", e)

        # Загрузка настроек
        settings = SettingsService()

        print("Settings loaded")
        print(f"Theme: {settings.get_theme()}")

        # Загрузка локализации
        try:
            get_locale().set_language(
                settings.get_language()
            )

        except Exception as e:
            print("Locale error:", e)

        # Обработка успешной авторизации
        def on_login_success(uid):

            print(f"LOGIN SUCCESS: {uid}")

            try:
                # Сохранение пользовательской сессии
                settings.save_user_session(uid)

                # Открытие главного окна
                window = MainWindow(uid, settings)
                window.show()

                # Сохранение ссылки на окно
                app.main_window = window

                print("MainWindow shown")

            except Exception as e:
                print("ERROR in MainWindow:", e)
                traceback.print_exc()

        # Проверка сохраненной сессии
        saved_user_id = settings.get_saved_user()

        # Автоматический вход
        if saved_user_id is not None:

            print(f"AUTO LOGIN: {saved_user_id}")

            try:
                # Открытие главного окна
                window = MainWindow(saved_user_id, settings)
                window.show()

                app.main_window = window

            except Exception as e:

                print("AUTOLOGIN ERROR:", e)
                traceback.print_exc()

                # Открытие окна логина при ошибке
                login = LoginWindow(
                    on_login_success=on_login_success
                )

                login.show()

                app.login_window = login

        else:
            # Открытие окна авторизации
            login = LoginWindow(
                on_login_success=on_login_success
            )

            login.show()

            app.login_window = login

        # Запуск основного цикла приложения
        sys.exit(app.exec_())

    except Exception as e:

        # Обработка критической ошибки
        print("FATAL ERROR:", e)

        traceback.print_exc()

        input("Press Enter to exit...")
import sys
import json
import os
import traceback

from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QApplication

from auth.login_window import LoginWindow
from ui.main_window import MainWindow
from services.settings_service import SettingsService
from locales.locale_manager import get_locale
from utils.resource_path import resource_path

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"


def load_session():
    try:
        with open(resource_path("session.json"), "r", encoding="utf-8") as f:
            return json.load(f).get("user_id")
    except:
        return None


def save_session(user_id):
    with open(resource_path("session.json"), "w", encoding="utf-8") as f:
        json.dump({"user_id": user_id}, f)


if __name__ == "__main__":
    print("APP STARTED")

    try:
        app = QApplication(sys.argv)
        print("QApplication created")

        # Иконка
        try:
            app.setWindowIcon(QIcon(resource_path("assets/img/icon.ico")))
        except Exception as e:
            print("⚠️ Icon error:", e)

        settings = SettingsService()
        print("Settings loaded")

        print(f"Theme: {settings.get_theme()}")

        # Язык
        try:
            get_locale().set_language(settings.get_language())
        except Exception as e:
            print("Locale error:", e)

        # ===== LOGIN SUCCESS =====
        def on_login_success(uid):
            print(f"LOGIN SUCCESS: {uid}")

            save_session(uid)

            try:
                window = MainWindow(uid, settings)  
                window.show()

                app.main_window = window

                print("MainWindow shown")

            except Exception as e:
                print("ERROR in MainWindow:", e)
                traceback.print_exc()

        login = LoginWindow(on_login_success=on_login_success)
        login.show()

        app.login_window = login

        sys.exit(app.exec_())

    except Exception as e:
        print("FATAL ERROR:", e)
        traceback.print_exc()
        input("Press Enter to exit...")
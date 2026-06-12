from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QLineEdit, QPushButton, QLabel, QTabWidget,
                             QMessageBox)
from PyQt5.QtCore import Qt
from core.db_handler import DBHandler
from locales.locale_manager import tr, get_locale
from services.settings_service import SettingsService


class LoginWindow(QMainWindow):
    def __init__(self, on_login_success):
        super().__init__()
        self.setWindowTitle("Posture Checker")
        self.resize(620, 520)
        self.setMinimumSize(620, 520)
        self.on_login_success = on_login_success

        self.db = DBHandler()
        self.settings_service = SettingsService()
        self.apply_theme()

        try:
            self.db.connect()
        except Exception as e:
            QMessageBox.critical(self, tr("error"), f"DB error: {e}")
            return

        self.init_ui()

        # Подключаем сигнал смены языка
        get_locale().language_changed.connect(self.retranslate_ui)

        # Загружаем сохраненный язык
        saved_lang = self.settings_service.get_language()
        get_locale().set_language(saved_lang)

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(20)

        # Кнопка переключения языка
        top_layout = QHBoxLayout()

        self.lang_btn = QPushButton()
        self.lang_btn.setObjectName("langButton")

        self.lang_btn.setMinimumWidth(130)
        self.lang_btn.setMinimumHeight(46)

        self.lang_btn.clicked.connect(self.toggle_language)

        top_layout.addStretch()
        top_layout.addWidget(self.lang_btn)

        main_layout.addLayout(top_layout)

        # main_layout.addSpacing(20)
        # main_layout.addWidget(self.hero_title)
        # main_layout.addWidget(self.hero_subtitle)
        # main_layout.addSpacing(10)

        # Вкладки
        self.tabs = QTabWidget()
        self.tabs.setObjectName("authTabs")

        # Вкладка входа
        self.login_widget = QWidget()
        login_layout = QVBoxLayout()

        self.login_user_label = QLabel()
        self.login_user = QLineEdit()
        self.login_user.setMinimumHeight(46)
        self.login_user.setPlaceholderText("username")

        self.login_pass_label = QLabel()
        self.login_pass = QLineEdit()
        self.login_pass.setMinimumHeight(46)
        self.login_pass.setPlaceholderText("password")
        self.login_pass.setEchoMode(QLineEdit.Password)

        self.btn_login = QPushButton()
        self.btn_login.clicked.connect(self.do_login)

        login_layout.addWidget(self.login_user_label)
        login_layout.addWidget(self.login_user)
        login_layout.addWidget(self.login_pass_label)
        login_layout.addWidget(self.login_pass)
        login_layout.addWidget(self.btn_login)
        login_layout.addStretch()

        self.login_widget.setLayout(login_layout)
        self.tabs.addTab(self.login_widget, "")

        # Вкладка регистрации
        self.reg_widget = QWidget()
        reg_layout = QVBoxLayout()

        self.reg_user_label = QLabel()
        self.reg_user = QLineEdit()
        self.reg_user.setMinimumHeight(46)
        self.reg_user.setPlaceholderText("username")

        self.reg_pass_label = QLabel()
        self.reg_pass = QLineEdit()
        self.reg_pass.setMinimumHeight(46)
        self.reg_pass.setPlaceholderText("password")
        self.reg_pass.setEchoMode(QLineEdit.Password)

        self.reg_pass2_label = QLabel()
        self.reg_pass2 = QLineEdit()
        self.reg_pass2.setMinimumHeight(46)
        self.reg_pass2.setPlaceholderText("confirm password")
        self.reg_pass2.setEchoMode(QLineEdit.Password)

        self.btn_register = QPushButton()
        self.btn_register.clicked.connect(self.do_register)

        reg_layout.addWidget(self.reg_user_label)
        reg_layout.addWidget(self.reg_user)
        reg_layout.addWidget(self.reg_pass_label)
        reg_layout.addWidget(self.reg_pass)
        reg_layout.addWidget(self.reg_pass2_label)
        reg_layout.addWidget(self.reg_pass2)
        reg_layout.addWidget(self.btn_register)
        reg_layout.addStretch()

        self.reg_widget.setLayout(reg_layout)
        self.tabs.addTab(self.reg_widget, "")

        main_layout.addWidget(self.tabs)
        central_widget.setLayout(main_layout)

        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновление текста при смене языка"""
        self.setWindowTitle(tr("app_title"))
        self.login_user_label.setText(tr("username"))
        self.login_pass_label.setText(tr("password"))
        self.btn_login.setText(tr("login_btn"))
        self.btn_login.setMinimumHeight(52)

        self.reg_user_label.setText(tr("username"))
        self.reg_pass_label.setText(tr("password"))
        self.reg_pass2_label.setText(tr("confirm_password"))
        self.btn_register.setText(tr("register_btn"))
        self.btn_register.setMinimumHeight(52)

        self.tabs.setTabText(0, tr("login"))
        self.tabs.setTabText(1, tr("register"))

        current_lang = get_locale().get_language()
        self.lang_btn.setText(tr("language_russian") if current_lang == "en" else tr("language_english"))

    def toggle_language(self):
        """Переключение языка"""
        current = get_locale().get_language()
        new_lang = "en" if current == "ru" else "ru"
        get_locale().set_language(new_lang)
        # Сохраняем язык в настройки
        self.settings_service.set_language(new_lang)

    def do_login(self):
        username = self.login_user.text().strip()
        password = self.login_pass.text()

        if not username or not password:
            QMessageBox.warning(self, tr("warning"), tr("fill_all_fields"))
            return

        user = self.db.authenticate_user(username, password)
        if user:
            QMessageBox.information(
                self,
                tr("success"),
                tr("login_success").format(username)
            )

            # СОХРАНЕНИЕ СЕССИИ
            self.settings_service.save_user_session(user['userid'], remember=False)

            self.on_login_success(user['userid'])
            self.close()
        else:
            QMessageBox.warning(self, tr("error"), tr("login_failed"))

    def do_register(self):
        username = self.reg_user.text().strip()
        password = self.reg_pass.text()
        password2 = self.reg_pass2.text()

        if not username or not password or not password2:
            QMessageBox.warning(self, tr("warning"), tr("fill_all_fields"))
            return

        if password != password2:
            QMessageBox.warning(self, tr("warning"), tr("passwords_not_match"))
            return

        user_id = self.db.register_user(username, password, "")
        if user_id:
            QMessageBox.information(self, tr("success"), tr("register_success"))
            self.reg_user.clear()
            self.reg_pass.clear()
            self.reg_pass2.clear()
        else:
            QMessageBox.warning(self, tr("error"), tr("register_failed"))

    def closeEvent(self, event):
        self.db.close()
        event.accept()

    def apply_theme(self):
        """Применение темы к окну авторизации"""

        theme = self.settings_service.get_theme()

        styles_path = (  
            "styles/style_dark.qss"
            if theme == "dark"
            else "styles/style_light.qss"
        )

        try:
            with open(styles_path, "r", encoding="utf-8") as f:
                self.setStyleSheet(f.read())
        except Exception as e:
            print("Theme load error:", e)
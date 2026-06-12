from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton, QSlider, QMessageBox,
                             QComboBox)
from PyQt5.QtCore import Qt, pyqtSignal
import os

from locales.locale_manager import tr, get_locale
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import QCheckBox

class SettingsPage(QWidget):
    theme_changed = pyqtSignal(str)
    accuracy_changed = pyqtSignal(float)
    language_changed = pyqtSignal(str)

    def __init__(self, db, session_manager, settings_service):
        super().__init__()

        self.db = db
        self.session_manager = session_manager
        self.settings_service = settings_service
        self._updating = False

        self.init_ui()

        # Подключаем сигнал смены языка
        get_locale().language_changed.connect(self.retranslate_ui)

        # Загружаем настройки после инициализации UI
        QTimer.singleShot(100, self.load_current_settings)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(20, 20, 20, 20)

        # Заголовок
        self.title = QLabel()
        self.title.setProperty("class", "title-main")
        layout.addWidget(self.title)

        # Карточка пользователя
        user_card = QFrame()
        user_card.setObjectName("card")
        user_layout = QVBoxLayout()
        user_layout.setSpacing(15)

        self.user_title = QLabel()
        self.user_title.setProperty("class", "title-card")
        user_layout.addWidget(self.user_title)

        self.user_info = QLabel()
        self.user_info.setProperty("class", "info-text")
        user_layout.addWidget(self.user_info)

        self.logout_btn = QPushButton()
        self.logout_btn.setObjectName("btnLogout")
        self.logout_btn.clicked.connect(self.logout)
        user_layout.addWidget(self.logout_btn)

        user_card.setLayout(user_layout)
        layout.addWidget(user_card)

        # Карточка языка
        lang_card = QFrame()
        lang_card.setObjectName("card")
        lang_layout = QVBoxLayout()
        lang_layout.setSpacing(15)

        self.lang_title = QLabel()
        self.lang_title.setProperty("class", "title-card")
        lang_layout.addWidget(self.lang_title)

        self.lang_combo = QComboBox()
        self.lang_combo.currentIndexChanged.connect(self.on_language_changed)
        lang_layout.addWidget(self.lang_combo)

        lang_card.setLayout(lang_layout)
        layout.addWidget(lang_card)

        # Карточка темы
        theme_card = QFrame()
        theme_card.setObjectName("card")
        theme_layout = QVBoxLayout()
        theme_layout.setSpacing(15)

        self.theme_title = QLabel()
        self.theme_title.setProperty("class", "title-card")
        theme_layout.addWidget(self.theme_title)

        self.theme_combo = QComboBox()
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        theme_layout.addWidget(self.theme_combo)

        theme_card.setLayout(theme_layout)
        layout.addWidget(theme_card)

        # Карточка точности
        # accuracy_card = QFrame()
        # accuracy_card.setObjectName("card")
        # accuracy_layout = QVBoxLayout()
        # accuracy_layout.setSpacing(15)

        # self.accuracy_title = QLabel()
        # self.accuracy_title.setProperty("class", "title-card")
        # accuracy_layout.addWidget(self.accuracy_title)

        # self.accuracy_desc = QLabel()
        # self.accuracy_desc.setProperty("class", "label-small")
        # self.accuracy_desc.setWordWrap(True)
        # accuracy_layout.addWidget(self.accuracy_desc)

        # self.accuracy_slider = QSlider(Qt.Horizontal)
        # self.accuracy_slider.setMinimum(0)
        # self.accuracy_slider.setMaximum(100)
        # self.accuracy_slider.setTickInterval(10)
        # self.accuracy_slider.valueChanged.connect(self.on_accuracy_changed)
        # accuracy_layout.addWidget(self.accuracy_slider)

        # self.accuracy_value = QLabel()
        # self.accuracy_value.setProperty("class", "accuracy-value")
        # self.accuracy_value.setAlignment(Qt.AlignCenter)
        # accuracy_layout.addWidget(self.accuracy_value)

        # hints_layout = QHBoxLayout()
        # self.hint_fast = QLabel()
        # hints_layout.addWidget(self.hint_fast)
        # hints_layout.addStretch()
        # self.hint_medium = QLabel()
        # hints_layout.addWidget(self.hint_medium)
        # hints_layout.addStretch()
        # self.hint_high = QLabel()
        # hints_layout.addWidget(self.hint_high)
        # accuracy_layout.addLayout(hints_layout)

        # accuracy_card.setLayout(accuracy_layout)
        # layout.addWidget(accuracy_card)

        # --- КАРТОЧКА СКЕЛЕТА ---
        skeleton_card = QFrame()
        skeleton_card.setObjectName("card")
        skeleton_layout = QVBoxLayout()
        skeleton_layout.setSpacing(15)

        self.skeleton_title = QLabel()
        self.skeleton_title.setProperty("class", "title-card")
        skeleton_layout.addWidget(self.skeleton_title)

        self.skeleton_checkbox = QCheckBox()
        self.skeleton_checkbox.stateChanged.connect(self.on_skeleton_changed)
        skeleton_layout.addWidget(self.skeleton_checkbox)

        skeleton_card.setLayout(skeleton_layout)
        layout.addWidget(skeleton_card)

        layout.addStretch()
        self.setLayout(layout)

        # Применяем переводы
        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновление текста при смене языка"""
        self.title.setText(tr("settings_title"))
        self.user_title.setText(tr("user_info"))
        self.logout_btn.setText(tr("logout_btn"))
        self.lang_title.setText(tr("language"))
        self.skeleton_title.setText(tr("show_skeleton"))
        self.skeleton_checkbox.setText(tr("enable_skeleton"))
        self.theme_title.setText(tr("theme_title"))
        # self.accuracy_title.setText(tr("accuracy_title"))
        # self.accuracy_desc.setText(tr("accuracy_desc"))

        # Обновляем элементы ComboBox без сигналов
        self.theme_combo.blockSignals(True)
        self.theme_combo.clear()
        self.theme_combo.addItem(tr("theme_light"))
        self.theme_combo.addItem(tr("theme_dark"))
        # Восстанавливаем выбор
        current_theme = self.settings_service.get_theme()
        self.theme_combo.setCurrentIndex(0 if current_theme == "light" else 1)
        self.theme_combo.blockSignals(False)

        self.lang_combo.blockSignals(True)
        current_lang_text = self.lang_combo.currentText()
        self.lang_combo.clear()
        self.lang_combo.addItem(tr("language_russian"), "ru")
        self.lang_combo.addItem(tr("language_english"), "en")
        # Восстанавливаем выбор
        current_lang = self.settings_service.get_language()
        for i in range(self.lang_combo.count()):
            if self.lang_combo.itemData(i) == current_lang:
                self.lang_combo.setCurrentIndex(i)
                break
        self.lang_combo.blockSignals(False)

        # self.hint_fast.setText(tr("accuracy_fast"))
        # self.hint_medium.setText(tr("accuracy_medium"))
        # self.hint_high.setText(tr("accuracy_high"))

        # Обновляем текущую точность
        # accuracy = self.settings_service.get_accuracy()
        # self.update_accuracy_label(accuracy)

    def load_current_settings(self):
        """Загрузка текущих настроек"""
        try:
            self._updating = True

            # Загружаем информацию о пользователе
            user_id = self.session_manager.current_user_id
            if user_id:
                user_data = self.db.get_user_by_id(user_id)
                if user_data:
                    self.user_info.setText(tr("user_name").format(user_data['username']))

            #Загружаем скелет
            self.skeleton_checkbox.setChecked(self.settings_service.get_show_skeleton())

            # Загружаем тему
            theme = self.settings_service.get_theme()
            self.theme_combo.setCurrentIndex(0 if theme == "light" else 1)

            # Загружаем язык
            language = self.settings_service.get_language()
            for i in range(self.lang_combo.count()):
                if self.lang_combo.itemData(i) == language:
                    self.lang_combo.setCurrentIndex(i)
                    break

            # Загружаем точность
            accuracy = self.settings_service.get_accuracy()
            self.accuracy_slider.setValue(int(accuracy * 100))
            self.update_accuracy_label(accuracy)

            self._updating = False
        except Exception as e:
            print(f"Ошибка загрузки настроек: {e}")
            self._updating = False

    def on_skeleton_changed(self, state):
        if self._updating:
            return

        value = state == Qt.Checked
        self.settings_service.set_show_skeleton(value)

    # def update_accuracy_label(self, accuracy):
    #     if accuracy >= 0.8:
    #         self.accuracy_value.setText(tr("accuracy_high"))
    #     elif accuracy >= 0.6:
    #         self.accuracy_value.setText(tr("accuracy_medium"))
    #     else:
    #         self.accuracy_value.setText(tr("accuracy_fast"))

    def on_language_changed(self, index):
        if self._updating:
            return
        lang_code = self.lang_combo.itemData(index)
        if lang_code:
            self.settings_service.set_language(lang_code)
            get_locale().set_language(lang_code)
            self.language_changed.emit(lang_code)

    def on_theme_changed(self, index):
        if self._updating:
            return
        theme = "light" if index == 0 else "dark"
        self.settings_service.set_theme(theme)
        self.theme_changed.emit(theme)

    def on_accuracy_changed(self, value):
        if self._updating:
            return
        accuracy = value / 100.0
        self.settings_service.set_accuracy(accuracy)
        self.update_accuracy_label(accuracy)
        self.accuracy_changed.emit(accuracy)

    def logout(self):
        reply = QMessageBox.question(
            self,
            tr("confirm_logout"),
            tr("confirm_logout_msg"),
            QMessageBox.Yes | QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.settings_service.clear_user_session()  # ✔️ ВОТ ЭТО ГЛАВНОЕ

            self.window().close()

            from auth.login_window import LoginWindow
            self.login_window = LoginWindow(
                on_login_success=lambda uid: self.restart_main_window(uid)
            )
            self.login_window.show()

    def restart_main_window(self, user_id):
        """Перезапуск главного окна после входа"""
        from ui.main_window import MainWindow
        self.main_window = MainWindow(user_id, self.settings_service)
        self.main_window.show()
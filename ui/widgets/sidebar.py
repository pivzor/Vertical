from PyQt5.QtWidgets import QWidget, QVBoxLayout, QPushButton
from PyQt5.QtCore import Qt
from locales.locale_manager import tr, get_locale


class Sidebar(QWidget):
    def __init__(self, on_change):
        super().__init__()
        self.setFixedWidth(250)
        self.on_change = on_change

        self.layout = QVBoxLayout()
        self.layout.setSpacing(15)
        self.layout.setContentsMargins(15, 20, 15, 20)
        self.buttons = {}

        # Создаем кнопки
        for key in ["dashboard", "monitor", "settings", "about"]:
            btn = QPushButton()
            btn.setMinimumHeight(50)
            btn.clicked.connect(lambda _, k=key: self.on_change(k))
            self.layout.addWidget(btn)
            self.buttons[key] = btn

        self.layout.addStretch()
        self.setLayout(self.layout)

        # Применяем переводы
        self.retranslate_ui()

        # Подключаем сигнал смены языка
        get_locale().language_changed.connect(self.retranslate_ui)

    def retranslate_ui(self):
        """Обновление текста кнопок при смене языка"""
        # icons = {
        #     "dashboard": "📊",
        #     "monitor": "🎥",
        #     "settings": "⚙️",
        #     "about": "ℹ️"
        # }

        titles = {
            "dashboard": tr("dashboard_title"),
            "monitor": tr("monitoring_title"),
            "settings": tr("settings_title"),
            "about": tr("about_title")
        }

        for key, btn in self.buttons.items():
            btn.setText(f"{titles[key]}")
            font = btn.font()
            font.setPointSize(10)
            btn.setFont(font)
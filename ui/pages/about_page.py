from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QFrame, QPushButton)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QDesktopServices
from PyQt5.QtCore import QUrl
from locales.locale_manager import tr, get_locale


class AboutPage(QWidget):
    def __init__(self):
        super().__init__()

        self.init_ui()

        # Подключаем сигнал смены языка
        get_locale().language_changed.connect(self.retranslate_ui)

    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Заголовок
        self.title = QLabel()
        self.title.setProperty("class", "title-main")
        self.title.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title)

        # Карточка с информацией о программе
        info_card = QFrame()
        info_card.setObjectName("card")
        info_layout = QVBoxLayout()
        info_layout.setSpacing(15)

        # Название программы
        self.app_name = QLabel()
        app_name_font = QFont()
        app_name_font.setPointSize(24)
        app_name_font.setBold(True)
        self.app_name.setFont(app_name_font)
        self.app_name.setAlignment(Qt.AlignCenter)
        info_layout.addWidget(self.app_name)

        # Версия
        self.version_label = QLabel()
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setProperty("class", "label-metrics")
        info_layout.addWidget(self.version_label)

        # Разделитель
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        info_layout.addWidget(line)

        # Описание программы
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setAlignment(Qt.AlignCenter)
        self.description.setProperty("class", "label-metrics")
        info_layout.addWidget(self.description)

        info_card.setLayout(info_layout)
        layout.addWidget(info_card)

        # Карточка с информацией об осанке
        posture_card = QFrame()
        posture_card.setObjectName("card")
        posture_layout = QVBoxLayout()
        posture_layout.setSpacing(15)

        self.posture_title = QLabel()
        posture_title_font = QFont()
        posture_title_font.setPointSize(18)
        posture_title_font.setBold(True)
        self.posture_title.setFont(posture_title_font)
        self.posture_title.setAlignment(Qt.AlignCenter)
        posture_layout.addWidget(self.posture_title)

        # Советы по осанке
        self.tips = QLabel()
        self.tips.setWordWrap(True)
        self.tips.setAlignment(Qt.AlignCenter)
        self.tips.setProperty("class", "label-metrics")
        posture_layout.addWidget(self.tips)

        posture_card.setLayout(posture_layout)
        layout.addWidget(posture_card)

        # Карточка с контактами
        contact_card = QFrame()
        contact_card.setObjectName("card")
        contact_layout = QVBoxLayout()
        contact_layout.setSpacing(15)

        self.contact_title = QLabel()
        contact_title_font = QFont()
        contact_title_font.setPointSize(14)
        contact_title_font.setBold(True)
        self.contact_title.setFont(contact_title_font)
        self.contact_title.setAlignment(Qt.AlignCenter)
        contact_layout.addWidget(self.contact_title)

        # Кнопка GitHub
        self.github_btn = QPushButton("GitHub")
        self.github_btn.setMinimumHeight(40)
        self.github_btn.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://github.com/pivzor")))
        contact_layout.addWidget(self.github_btn)

        # Email
        self.email_label = QLabel("veltical@gmail.com")
        self.email_label.setAlignment(Qt.AlignCenter)
        self.email_label.setProperty("class", "label-metrics")
        contact_layout.addWidget(self.email_label)

        contact_card.setLayout(contact_layout)
        layout.addWidget(contact_card)

        layout.addStretch()
        self.setLayout(layout)

        # Применяем переводы
        self.retranslate_ui()

    def retranslate_ui(self):
        """Обновление текста при смене языка"""
        self.title.setText(tr("about_title"))
        self.app_name.setText(tr("app_title"))
        self.version_label.setText(tr("version").format("1.0.0"))
        self.description.setText(tr("about_description"))
        self.posture_title.setText(tr("posture_tips_title"))
        self.tips.setText(tr("posture_tips"))
        self.contact_title.setText(tr("contacts"))
        self.github_btn.setText(tr("github_link"))
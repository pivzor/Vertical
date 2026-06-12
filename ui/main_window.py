from PyQt5.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QStackedWidget, QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication

from ui.widgets.sidebar import Sidebar
from ui.pages.dashboard_page import DashboardPage
from ui.pages.monitoring_page import MonitoringPage
from ui.pages.settings_page import SettingsPage
from ui.pages.about_page import AboutPage

from core.db_handler import DBHandler
from core.session_manager import SessionManager
from services.realtime_analyzer import RealtimeAnalyzer
from services.settings_service import SettingsService
from locales.locale_manager import get_locale, tr
from utils.resource_path import resource_path


class MainWindow(QMainWindow):
    def __init__(self, user_id, settings_service):
        super().__init__()

        screen = QApplication.primaryScreen()
        size = screen.availableGeometry()

        w = int(size.width() * 0.82)
        h = int(size.height() * 0.82)

        self.resize(w, h)

        self.setWindowTitle("Posture App")
        self.resize(1700, 950)
        self.setMinimumSize(1400, 850)
        self.setAttribute(Qt.WA_StyledBackground, True)

        # ===== SERVICES =====
        self.db = DBHandler()
        self.db.connect()

        self.session_manager = SessionManager()
        self.session_manager.current_user_id = user_id

        self.analyzer = RealtimeAnalyzer()

        self.settings_service = settings_service

        # ===== LANGUAGE =====
        get_locale().set_language(self.settings_service.get_language())
        get_locale().language_changed.connect(self.retranslate_ui)

        # ===== UI =====
        self.stack = QStackedWidget()
        self.pages = {}

        sidebar = Sidebar(self.switch_page)

        container = QWidget()
        container.setAttribute(Qt.WA_StyledBackground, True)

        layout = QHBoxLayout()
        layout.addWidget(sidebar)
        layout.addWidget(self.stack)
        container.setLayout(layout)

        self.setCentralWidget(container)

        self.apply_theme(self.settings_service.get_theme())

        self.switch_page("dashboard")
        self.retranslate_ui()


    def apply_theme(self, theme):
        css_file = resource_path(
            f"styles/style_{theme}.qss"
        )

        try:
            with open(css_file, "r", encoding="utf-8") as f:
                style = f.read()

            app = QApplication.instance()

            app.setStyleSheet("")
            app.processEvents()
            app.setStyleSheet(style)

        except Exception as e:
            print(f"Ошибка загрузки темы: {e}")

    def change_theme(self, theme):
        self.settings_service.set_theme(theme)
        self.apply_theme(theme)

    # =========================
    # PAGES
    # =========================
    def get_page(self, name):
        if name in self.pages:
            return self.pages[name]

        if name == "dashboard":
            page = DashboardPage(
                self.analyzer,
                self.db,
                self.session_manager.current_user_id,
                self.settings_service
            )

        elif name == "monitor":
            page = MonitoringPage(
                self.session_manager,
                self.db,
                self.analyzer,
                self.settings_service
            )

        elif name == "settings":
            page = SettingsPage(
                self.db,
                self.session_manager,
                self.settings_service
            )

            page.theme_changed.connect(self.change_theme)
            page.accuracy_changed.connect(self.change_accuracy)
            page.language_changed.connect(self.change_language)

        elif name == "about":
            page = AboutPage()
        else:
            return None

        self.pages[name] = page
        self.stack.addWidget(page)

        return page

    def switch_page(self, name):
        page = self.get_page(name)
        if page:
            self.stack.setCurrentWidget(page)

    # =========================
    # LANGUAGE
    # =========================
    def retranslate_ui(self):
        self.setWindowTitle(tr("app_title"))

        for page in self.pages.values():
            if hasattr(page, "retranslate_ui"):
                page.retranslate_ui()

    def change_language(self, lang):
        self.settings_service.set_language(lang)
        self.retranslate_ui()

    # =========================
    # OTHER SETTINGS
    # =========================
    def change_accuracy(self, accuracy):
        self.settings_service.set_accuracy(accuracy)

        config = self.settings_service.get_posture_config()

        monitor_page = self.pages.get("monitor")
        if monitor_page and hasattr(monitor_page, "camera") and monitor_page.camera:
            if hasattr(monitor_page.camera, "update_accuracy"):
                monitor_page.camera.update_accuracy(config)
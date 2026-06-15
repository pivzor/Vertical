from PyQt5.QtWidgets import (
    QSizePolicy, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QMessageBox, QComboBox
)
from PyQt5.QtCore import Qt, QTimer

from camera.camera_widget import CameraWidget
from locales.locale_manager import tr, get_locale

import cv2

from PyQt5.QtWidgets import QSystemTrayIcon, QStyle
from PyQt5.QtCore import QDateTime
from win10toast import ToastNotifier
from utils.resource_path import resource_path


class MonitoringPage(QWidget):
    def __init__(self, session_manager, db, analyzer, settings_service):
        super().__init__()

        self.session_manager = session_manager
        self.db = db
        self.analyzer = analyzer
        self.settings_service = settings_service
        self.user_id = self.session_manager.current_user_id

        self.session_active = False
        self.camera = None
        self.current_session_id = None

        self.smooth_buffer = []
        self.toaster = ToastNotifier()

        self.last_notify_time = (
            QDateTime.currentDateTime().addSecs(-60)
        )

        self.last_notify_time = QDateTime.currentDateTime().addSecs(-60)

        self.init_ui()

        get_locale().language_changed.connect(self.retranslate_ui)


        QTimer.singleShot(100, self.load_cameras)

    #UI
    def init_ui(self):
        main_layout = QHBoxLayout()
        main_layout.setSpacing(20)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # LEFT (видео)
        left = QFrame()
        left.setObjectName("card")

        left_layout = QVBoxLayout()
        left_layout.setAlignment(Qt.AlignTop)

        self.video_title = QLabel()
        self.video_title.setProperty("class", "title-card")
        left_layout.addWidget(self.video_title)

        self.video_container = QFrame()
        self.video_container.setObjectName("videoContainer")

        self.video_layout = QVBoxLayout()
        self.video_layout.setContentsMargins(0, 0, 0, 0)

        self.video_container.setMinimumHeight(700)
        self.video_container.setSizePolicy(
            QSizePolicy.Expanding,
            QSizePolicy.Expanding
        )
        self.video_container.setLayout(self.video_layout)

        left_layout.addWidget(self.video_container)
        left.setLayout(left_layout)

        main_layout.addWidget(left, 5)

        # RIGHT (панель)
        right = QFrame()
        right.setObjectName("card")

        right_layout = QVBoxLayout()
        right_layout.setSpacing(15)

        self.title = QLabel()
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setProperty("class", "title-metrics")
        right_layout.addWidget(self.title)

        # CAMERA
        self.camera_selector = QComboBox()
        self.camera_selector.currentIndexChanged.connect(
            self.on_camera_changed
        )
        right_layout.addWidget(self.camera_selector)

        # MODE
        self.mode_selector = QComboBox()
        self.mode_selector.addItem(tr("mode_front"), "front")
        self.mode_selector.addItem(tr("mode_side"), "side")
        self.mode_selector.currentIndexChanged.connect(
            self.on_mode_changed
        )
        right_layout.addWidget(self.mode_selector)

        # STATUS
        self.status_label = QLabel()
        self.status_label.setAlignment(Qt.AlignCenter)
        right_layout.addWidget(self.status_label)

        # ТЕКУЩИЙ БАЛЛ
        self.score_title = QLabel(tr("current_score"))
        self.score_title.setAlignment(Qt.AlignCenter)
        self.score_title.setProperty("class", "label-metrics")
        right_layout.addWidget(self.score_title)

        self.score_label = QLabel("---")
        self.score_label.setAlignment(Qt.AlignCenter)
        self.score_label.setMinimumHeight(140)

        self.score_label.setStyleSheet("""
            QLabel {
                background-color: #374151;
                color: white;
                border-radius: 20px;
                font-size: 96px;
                font-weight: 900;
            }
        """)

        right_layout.addWidget(self.score_label)

        # СОСТОЯНИЕ ОСАНКИ
        self.status_text = QLabel("---")
        self.status_text.setAlignment(Qt.AlignCenter)
        self.status_text.setMinimumHeight(70)

        self.status_text.setStyleSheet("""
            QLabel {
                background-color: #374151;
                color: white;
                border-radius: 14px;
                padding: 10px;
                font-size: 28px;
                font-weight: 800;
            }
        """)

        right_layout.addWidget(self.status_text)

        right_layout.addStretch()

        # BUTTONS
        self.start_btn = QPushButton()
        self.start_btn.clicked.connect(
            self.start_monitoring
        )
        right_layout.addWidget(self.start_btn)

        self.stop_btn = QPushButton()
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(
            self.stop_monitoring
        )
        right_layout.addWidget(self.stop_btn)

        right.setLayout(right_layout)

        main_layout.addWidget(right, 2)

        self.setLayout(main_layout)

        self.retranslate_ui()

    #CAMERAS
    def load_cameras(self):
        self.camera_selector.clear()

        found = False
        for i in range(2): 
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                self.camera_selector.addItem(f"{tr('camera')} {i}", i)
                cap.release()
                found = True

        if not found:
            self.camera_selector.addItem(tr("camera_not_found"), -1)

    def on_camera_changed(self):
        cam_id = self.camera_selector.currentData()
        if self.camera and cam_id != -1:
            self.camera.set_camera(cam_id)

    #MODE
    def on_mode_changed(self):
        if self.camera:
            self.camera.service.set_mode(self.mode_selector.currentData())

    #START
    def start_monitoring(self):
        if self.session_active:
            QMessageBox.warning(self, tr("warning"), tr("monitoring_active"))
            return

        try:
            self.current_session_id = self.db.start_session(self.user_id)

            if not self.current_session_id:
                QMessageBox.critical(self, tr("error"), tr("session_create_error"))
                return

            self.session_manager.start_session(self.user_id, self.current_session_id)

            self.session_active = True

            self.status_label.setText(tr("status_active"))
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)

            self.analyzer.scores.clear()
            self.smooth_buffer.clear()

            QTimer.singleShot(50, self.init_camera)

        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    def init_camera(self):
        self.camera = CameraWidget(
            self.session_manager,
            self.db,
            self.settings_service
        )

        self.camera.set_show_skeleton(
            self.settings_service.get_show_skeleton()
        )

        self.camera.posture_updated.connect(self.on_posture_update)
        self.video_layout.addWidget(self.camera)

    #STOP
    def stop_monitoring(self):
        if not self.session_active:
            return

        try:
            reply = QMessageBox.question(
                self,
                tr("session_end_confirm"),
                tr("session_end_msg").format(
                    self.current_session_id,
                    self.analyzer.get_avg(),
                    # len(self.analyzer.scores)
                ),
                QMessageBox.Yes | QMessageBox.No
            )

            if reply != QMessageBox.Yes:
                return

            try:
                if self.current_session_id:
                    self.db.end_session(self.current_session_id)
                    self.db.add_log(self.user_id, f"Session #{self.current_session_id} ended")
            except Exception as e:
                print("DB save error:", e)

            if self.camera:
                self.camera.close()
                self.camera = None

            while self.video_layout.count():
                item = self.video_layout.takeAt(0)
                if item.widget():
                    item.widget().deleteLater()

            self.session_active = False
            self.start_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

            self.status_label.setText(tr("status_completed"))
            self.current_session_id = None


        except Exception as e:
            QMessageBox.critical(self, tr("error"), str(e))

    #POSTURE
    def on_posture_update(self, score, status):
        if not self.session_active:
            return

        self.analyzer.add_score(score)

        # try:
        #     self.db.add_pose_data(
        #         self.current_session_id,
        #         neck_angle=score,
        #         posture_status=status,
        #         keypoints=[]
        #     )
        # except Exception as e:
        #     print("DB save error:", e)

        # self.last_score = int(score)

        # Цветовая схема
        if score >= 85:
            text = tr("posture_excellent")
            color = "#16a34a"      # зеленый

        elif score >= 75:
            text = tr("posture_good")
            color = "#eab308"      # желтый

        elif score >= 55:
            text = tr("posture_slight")
            color = "#f97316"      # оранжевый

        else:
            text = tr("posture_bad")
            color = "#dc2626"      # красный

        # Балл
        self.score_label.setText(str(int(score)))

        self.score_label.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 20px;
                font-size: 96px;
                font-weight: 900;
            }}
        """)

        # Текст состояния
        self.status_text.setText(text)

        self.status_text.setStyleSheet(f"""
            QLabel {{
                background-color: {color};
                color: white;
                border-radius: 14px;
                padding: 10px;
                font-size: 28px;
                font-weight: 800;
            }}
        """)

        # УВЕДОМЛЕНИЯ

        is_bad = score < 60

        main_window = self.window()

        app_in_background = (
            main_window.isMinimized()
            or not main_window.isActiveWindow()
        )

        now = QDateTime.currentDateTime()

        if is_bad and app_in_background:
            if self.last_notify_time.secsTo(now) > 25:
                self.show_notification(
                    tr("warning"),
                    tr("session_end_bad")
                )
                self.last_notify_time = now

    def show_notification(self, title, message):

        try:
            self.toaster.show_toast(
                title,
                message,
                icon_path=resource_path("assets/img/icon.ico"),
                duration=3,
                threaded=True
            )

        except Exception as e:
            print("Notification error:", e)

    #UI
    def retranslate_ui(self):
        self.video_title.setText(tr("video_stream"))
        self.title.setText(tr("monitoring_title"))

        self.start_btn.setText(tr("start_monitoring"))
        self.stop_btn.setText(tr("stop_monitoring"))

        if self.session_active:
            self.status_label.setText(tr("status_active"))
        else:
            self.status_label.setText(tr("status_inactive"))
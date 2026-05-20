import cv2
import mediapipe as mp

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from services.posture_service import PostureService


class CameraWidget(QWidget):
    posture_updated = pyqtSignal(int, str)

    def __init__(self, session_manager, db, settings_service):
        super().__init__()

        self.session_manager = session_manager
        self.db = db
        self.settings_service = settings_service

        # камера по умолчанию
        self.cap = cv2.VideoCapture(0)

        # сервис осанки
        self.service = PostureService()

        # настройка скелета из settings
        self.show_skeleton = self.settings_service.get_show_skeleton()

        # UI
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # таймер
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)

    # ================= CAMERA SWITCH =================
    def set_camera(self, index: int):
        if self.cap.isOpened():
            self.cap.release()

        self.cap = cv2.VideoCapture(index)

    # ================= SKELETON TOGGLE (FIX ERROR) =================
    def set_show_skeleton(self, value: bool):
        self.show_skeleton = value

    # ================= MAIN LOOP =================
    def update_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            return

        keypoints, score, status, result = self.service.analyze(frame)

        if result.pose_landmarks and self.show_skeleton:
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.service.mp_pose.POSE_CONNECTIONS
            )

        if keypoints:
            self.session_manager.add_frame_data(
                keypoints=keypoints,
                angle=getattr(self.service, "last_angle", None),
                status=status,
                score=score
            )

            try:
                self.db.add_pose_data(
                    self.session_manager.current_session_id,
                    neck_angle=score,
                    posture_status=status,
                    keypoints=keypoints
                )
            except Exception as e:
                print("DB error:", e)

            self.posture_updated.emit(score, status)

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb.shape

        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

        self.label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.label.width(),
                self.label.height(),
                Qt.KeepAspectRatio
            )
        )

    def closeEvent(self, event):
        if self.cap and self.cap.isOpened():
            self.cap.release()
        event.accept()
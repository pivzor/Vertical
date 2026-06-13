import cv2
import mediapipe as mp

from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap

from services.posture_service import PostureService


class CameraWidget(QWidget):
    # Сигнал обновления оценки осанки
    posture_updated = pyqtSignal(int, str)

    def __init__(self, session_manager, db, settings_service):
        super().__init__()

        # Менеджер текущей сессии
        self.session_manager = session_manager

        # Подключение к БД
        self.db = db

        # Сервис настроек
        self.settings_service = settings_service

        # Подключение камеры по умолчанию
        self.cap = cv2.VideoCapture(0)

        # Сервис анализа осанки
        self.service = PostureService()

        # Настройка отображения скелета
        self.show_skeleton = self.settings_service.get_show_skeleton()

        # Область вывода видеопотока
        self.label = QLabel()
        self.label.setAlignment(Qt.AlignCenter)

        # Основной layout
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)

        # Таймер обновления кадров
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)#кадр/сек

    # Переключение камеры
    def set_camera(self, index: int):

        # Освобождение предыдущей камеры
        if self.cap.isOpened():
            self.cap.release()

        # Подключение новой камеры
        self.cap = cv2.VideoCapture(index)

    # Включение/выключение скелета
    def set_show_skeleton(self, value: bool):
        self.show_skeleton = value

    # Обработка нового кадра
    def update_frame(self):

        # Получение кадра с камеры
        ret, frame = self.cap.read()

        # Проверка успешного чтения
        if not ret:
            return

        # Анализ осанки
        keypoints, score, status, result = self.service.analyze(frame)

        # Отрисовка скелета пользователя
        if result.pose_landmarks and self.show_skeleton:
            mp.solutions.drawing_utils.draw_landmarks(
                frame,
                result.pose_landmarks,
                self.service.mp_pose.POSE_CONNECTIONS
            )

        # Проверка наличия ключевых точек
        if keypoints:

            # Сохранение данных кадра в сессию
            self.session_manager.add_frame_data(
                keypoints=keypoints,
                angle=getattr(self.service, "last_angle", None),
                status=status,
                score=score
            )

            try:
                # Сохранение данных в БД
                self.db.add_pose_data(
                    self.session_manager.current_session_id,
                    neck_angle=score,
                    posture_status=status,
                    keypoints=keypoints
                )

            # Обработка ошибки БД
            except Exception as e:
                print("DB error:", e)

            # Отправка сигнала обновления UI
            self.posture_updated.emit(score, status)

        # Преобразование BGR → RGB
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Получение размеров изображения
        h, w, ch = rgb.shape

        # Создание изображения Qt
        img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)

        # Отображение кадра в интерфейсе
        self.label.setPixmap(
            QPixmap.fromImage(img).scaled(
                self.label.width(),
                self.label.height(),
                Qt.KeepAspectRatio
            )
        )

    # Освобождение камеры при закрытии
    def closeEvent(self, event):

        if self.cap and self.cap.isOpened():
            self.cap.release()

        event.accept()
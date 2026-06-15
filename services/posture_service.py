import mediapipe as mp
import math
from collections import deque
from locales.locale_manager import tr


class PostureService:
    def __init__(self, accuracy=0.6):

        # Модуль MediaPipe Pose
        self.mp_pose = mp.solutions.pose

        # Коэффициент точности анализа
        self.accuracy = accuracy

        # Инициализация модели распознавания позы
        self.pose = self._create_pose()

        # Буфер сглаживания оценок осанки
        self.score_buffer = deque(maxlen=15)

        # Последний вычисленный угол шеи
        self.last_angle = 180

        # Режим анализа (front / side)
        self.mode = "front"

    # Установка режима анализа
    def set_mode(self, mode: str):
        self.mode = mode

    # Создание модели MediaPipe Pose
    def _create_pose(self):

        return self.mp_pose.Pose(

            # Упрощённая модель для уменьшения нагрузки
            model_complexity=0,

            # Минимальная уверенность обнаружения человека
            min_detection_confidence=0.5,

            # Минимальная уверенность отслеживания
            min_tracking_confidence=0.5
        )

    # Сглаживание колебаний оценки осанки
    def _smooth(self, score):

        self.score_buffer.append(score)

        return sum(self.score_buffer) / len(self.score_buffer)

    # Анализ положения пользователя спереди
    def _front(self, lm):

        # Ключевые точки тела
        nose = lm[self.mp_pose.PoseLandmark.NOSE.value]
        l_sh = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        r_sh = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        # Центр между плечами
        mid_sh_x = (l_sh.x + r_sh.x) / 2

        # Смещение головы относительно центра плеч
        head_offset = abs(nose.x - mid_sh_x)

        # Разница высоты плеч
        shoulder_tilt = abs(l_sh.y - r_sh.y)

        # Начальная оценка
        score = 100

        # Штраф за смещение головы
        score -= head_offset * 450

        # Штраф за перекос плеч
        score -= shoulder_tilt * 350

        return score, "front"

    # Анализ положения пользователя сбоку
    def _side(self, lm):

        # Оценка видимости левой стороны тела
        left_score = (
            lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].visibility +
            lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].visibility +
            lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].visibility
        )

        # Оценка видимости правой стороны тела
        right_score = (
            lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].visibility +
            lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value].visibility +
            lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].visibility
        )

        # Выбор наиболее видимой стороны
        use_right = right_score > left_score

        if use_right:

            ear = lm[self.mp_pose.PoseLandmark.RIGHT_EAR.value]
            shoulder = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            hip = lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            knee = lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value]

        else:

            ear = lm[self.mp_pose.PoseLandmark.LEFT_EAR.value]
            shoulder = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            hip = lm[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            knee = lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value]

        # Проверка видимости всех точек
        for p in (ear, shoulder, hip, knee):

            if p.visibility < 0.5:
                return None, tr("posture_bad_visibility")

        # Высота корпуса
        body_height = abs(shoulder.y - hip.y)

        # Проверка корректности данных
        if body_height < 0.05:
            return None, tr("posture_bad_visibility")

        # Смещение головы вперёд
        head_forward = abs(ear.x - shoulder.x) / body_height

        # Смещение плеч вперёд
        shoulder_forward = abs(shoulder.x - hip.x) / body_height

        # Смещение таза
        hip_shift = abs(hip.x - knee.x) / body_height

        # Угол шеи
        neck_angle = self.calculate_angle(
            (ear.x, ear.y),
            (shoulder.x, shoulder.y),
            (hip.x, hip.y)
        )

        # Угол спины
        back_angle = self.calculate_angle(
            (shoulder.x, shoulder.y),
            (hip.x, hip.y),
            (knee.x, knee.y)
        )

        # Сохранение последнего угла шеи
        self.last_angle = neck_angle

        # Начальная оценка
        score = 100

        # Штраф за положение головы
        score -= head_forward * 18

        # Штраф за положение плеч
        score -= shoulder_forward * 22

        # Штраф за положение таза
        score -= hip_shift * 12

        # Штраф за угол шеи
        if neck_angle < 140:
            score -= (140 - neck_angle) * 0.8

        # Штраф за угол спины
        if back_angle < 160:
            score -= (160 - back_angle) * 0.7

        return score, "side"

    # Вычисление угла между тремя точками
    def calculate_angle(self, a, b, c):

        ax, ay = a
        bx, by = b
        cx, cy = c

        # Формирование векторов
        ab = (ax - bx, ay - by)
        cb = (cx - bx, cy - by)

        # Скалярное произведение
        dot = ab[0] * cb[0] + ab[1] * cb[1]

        # Длины векторов
        mag1 = math.hypot(ab[0], ab[1])
        mag2 = math.hypot(cb[0], cb[1])

        # Защита от деления на ноль
        if mag1 * mag2 == 0:
            return 180

        # Косинус угла
        cos_angle = dot / (mag1 * mag2)

        # Ограничение диапазона
        cos_angle = max(-1, min(1, cos_angle))

        # Перевод в градусы
        return math.degrees(math.acos(cos_angle))

    # Анализ одного кадра изображения
    def analyze(self, frame):

        # Преобразование изображения BGR → RGB
        rgb = frame[:, :, ::-1]

        # Обработка изображения моделью
        result = self.pose.process(rgb)

        # Проверка наличия человека в кадре
        if not result.pose_landmarks:
            return None, 0, tr("posture_no_person"), result

        # Получение списка ключевых точек
        lm = result.pose_landmarks.landmark

        # Выбор режима анализа
        if self.mode == "front":
            raw_score, status = self._front(lm)
        else:
            raw_score, status = self._side(lm)

        # Проверка корректности результата
        if raw_score is None:
            return None, 0, status, result

        # Сглаживание оценки
        score = int(self._smooth(raw_score))

        # Ограничение диапазона значений
        score = max(0, min(100, score))

        # Определение текстового состояния осанки
        if score >= 85:
            status = tr("posture_excellent")

        elif score >= 75:
            status = tr("posture_good")

        elif score >= 55:
            status = tr("posture_slight")

        elif score >= 40:
            status = tr("posture_slouch")

        else:
            status = tr("posture_bad")

        # Сохранение координат ключевых точек
        keypoints = [(p.x, p.y, p.z) for p in lm]

        return keypoints, score, status, result
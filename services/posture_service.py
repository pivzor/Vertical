import mediapipe as mp
import math
from collections import deque
from locales.locale_manager import tr


class PostureService:
    def __init__(self, accuracy=0.6):
        self.mp_pose = mp.solutions.pose
        self.accuracy = accuracy

        #Инициализация модели распознавания позы
        self.pose = self._create_pose()

        #Буфер для сглаживания оценки осанки
        self.score_buffer = deque(maxlen=35)

        #Последний вычисленный угол шеи
        self.last_angle = 180

        #Режим анализа: front / side
        self.mode = "front"

    #Установка режима анализа
    def set_mode(self, mode: str):
        self.mode = mode

    #Создание модели MediaPipe Pose
    def _create_pose(self):
        return self.mp_pose.Pose(
            model_complexity=2,
            min_detection_confidence=0.3 + self.accuracy * 0.5,
            min_tracking_confidence=0.3 + self.accuracy * 0.5
        )

    #Сглаживание резких изменений оценки
    def _smooth(self, score):
        self.score_buffer.append(score)
        return sum(self.score_buffer) / len(self.score_buffer)

    #Анализ осанки спереди
    def _front(self, lm):

        #Ключевые точки тела
        nose = lm[self.mp_pose.PoseLandmark.NOSE.value]
        l_sh = lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
        r_sh = lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]

        #Центральная точка между плечами
        mid_sh_x = (l_sh.x + r_sh.x) / 2
        #mid_sh_y = (l_sh.y + r_sh.y) / 2

        #Смещение головы относительно центра плеч
        head_offset = abs(nose.x - mid_sh_x)

        #Перекос плеч
        shoulder_tilt = abs(l_sh.y - r_sh.y)

        #Начальная оценка осанки
        score = 100

        #Снижение оценки при наклоне головы
        score -= head_offset * 450

        #Снижение оценки при перекосе плеч
        score -= shoulder_tilt * 350

        return score, "front"

    def _side(self, lm):

        left_score = (
            lm[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value].visibility +
            lm[self.mp_pose.PoseLandmark.LEFT_HIP.value].visibility +
            lm[self.mp_pose.PoseLandmark.LEFT_KNEE.value].visibility
        )

        right_score = (
            lm[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value].visibility +
            lm[self.mp_pose.PoseLandmark.RIGHT_HIP.value].visibility +
            lm[self.mp_pose.PoseLandmark.RIGHT_KNEE.value].visibility
        )

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

        points = [ear, shoulder, hip, knee]

        for p in points:
            if p.visibility < 0.5:
                return None, tr("posture_bad_visibility")


        body_height = abs(shoulder.y - hip.y)

        if body_height < 0.05:
            return None, tr("posture_bad_visibility")

        head_forward = abs(ear.x - shoulder.x) / body_height
        shoulder_forward = abs(shoulder.x - hip.x) / body_height
        hip_shift = abs(hip.x - knee.x) / body_height


        neck_angle = self.calculate_angle(
            (ear.x, ear.y),
            (shoulder.x, shoulder.y),
            (hip.x, hip.y)
        )

        back_angle = self.calculate_angle(
            (shoulder.x, shoulder.y),
            (hip.x, hip.y),
            (knee.x, knee.y)
        )

        self.last_angle = neck_angle


        score = 100
        # голова
        score -= head_forward * 18
        # плечи
        score -= shoulder_forward * 22
        # таз
        score -= hip_shift * 12
        # шея
        if neck_angle < 140:
            score -= (140 - neck_angle) * 0.8
        # спина
        if back_angle < 160:
            score -= (160 - back_angle) * 0.7

        return score, "side"
    
    #Вычисление угла между тремя точками
    def calculate_angle(self, a, b, c):
        ax, ay = a
        bx, by = b
        cx, cy = c

        #Формирование векторов
        ab = (ax - bx, ay - by)
        cb = (cx - bx, cy - by)

        #Скалярное произведение векторов
        dot = ab[0] * cb[0] + ab[1] * cb[1]

        #Вычисление длин векторов
        mag1 = math.sqrt(ab[0] ** 2 + ab[1] ** 2)
        mag2 = math.sqrt(cb[0] ** 2 + cb[1] ** 2)

        #Проверка деления на ноль
        if mag1 * mag2 == 0:
            return 180

        #Вычисление угла
        angle = math.degrees(
            math.acos(dot / (mag1 * mag2))
        )

        return angle
        
    #Основной метод анализа кадра
    def analyze(self, frame):

        #Преобразование изображения из BGR в RGB
        rgb = frame[:, :, ::-1]

        #Обработка изображения моделью MediaPipe
        result = self.pose.process(rgb)

        #Проверка наличия человека в кадре
        if not result.pose_landmarks:
            return None, 0, tr("posture_no_person"), result

        #Получение ключевых точек тела
        lm = result.pose_landmarks.landmark

        #Выбор режима анализа
        if self.mode == "front":
            raw_score, status = self._front(lm)
        else:
            raw_score, status = self._side(lm)

        if raw_score is None:
            return None, 0, status, result

        #Сглаживание итоговой оценки
        score = int(self._smooth(raw_score))

        #Ограничение диапазона значений
        score = max(0, min(100, score))

        #Определение текстового состояния осанки
        if score >= 85:
            status = tr("posture_excellent")

        elif score >= 75:
            status = tr("posture_good")

        elif score >= 55:
            status = tr("posture_slight")

        elif score >= 40:
            status = tr("posture_slouch")


        #Сохранение координат ключевых точек
        keypoints = [(p.x, p.y, p.z) for p in lm]

        return keypoints, score, status, result
from collections import deque
import statistics


class RealtimeAnalyzer:
    def __init__(self):

        #Буфер хранения оценок осанки
        self.scores = deque(maxlen=200)

    #Добавление новой оценки
    def add_score(self, score):

        #Проверка отсутствия значения
        if score is None:
            return

        #Проверка корректности типа данных
        if isinstance(score, str):
            return

        #Проверка допустимого диапазона
        if score < 0:
            return

        #Ограничение диапазона значений
        score = max(0, min(100, float(score)))

        #Сохранение оценки
        self.scores.append(score)

    #Получение списка всех оценок
    def get_scores(self):
        return list(self.scores)

    #Вычисление средней оценки
    def get_avg(self):

        #Проверка наличия данных
        if not self.scores:
            return 0

        #Сортировка значений
        sorted_scores = sorted(self.scores)

        #Удаление крайних значений для уменьшения шумов
        trimmed = sorted_scores[
            int(len(sorted_scores) * 0.1):
            int(len(sorted_scores) * 0.9)
        ]

        #Вычисление среднего значения
        return round(statistics.mean(trimmed), 2) if trimmed else 0

    #Получение минимального значения
    def get_min(self):
        return min(self.scores) if self.scores else 0

    #Получение максимального значения
    def get_max(self):
        return max(self.scores) if self.scores else 0

    #Очистка буфера оценок
    def clear(self):
        self.scores.clear()
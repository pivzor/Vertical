import unittest

from services.posture_service import PostureService
from services.realtime_analyzer import RealtimeAnalyzer


class TestPostureService(unittest.TestCase):

    # Проверка вычисления угла 90 градусов
    def test_calculate_angle_90(self):

        service = PostureService.__new__(PostureService)

        angle = service.calculate_angle(
            (0, 1),
            (0, 0),
            (1, 0)
        )

        self.assertAlmostEqual(angle, 90, delta=1)


class TestRealtimeAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RealtimeAnalyzer()

    # Проверка ограничения диапазона
    def test_score_limit(self):

        self.analyzer.add_score(150)

        result = self.analyzer.get_scores()[0]

        self.assertEqual(result, 100)

    # Проверка обработки строковых данных
    def test_invalid_data(self):

        self.analyzer.add_score("error")

        self.assertEqual(
            len(self.analyzer.get_scores()),
            0
        )


if __name__ == "__main__":
    unittest.main()
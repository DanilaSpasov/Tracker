from datetime import datetime
from datetime import time
from datetime import timedelta
from unittest.mock import Mock
from unittest.mock import patch
from zoneinfo import ZoneInfo

from django.test import TestCase
from django.test import override_settings
from requests import RequestException

from habits.models import Habit
from telegram_bot.services import send_telegram_message
from telegram_bot.tasks import build_habit_message
from telegram_bot.tasks import send_habit_reminders
from users.models import User


@override_settings(TELEGRAM_BOT_TOKEN="test-token")
class TelegramServiceTestCase(TestCase):
    @patch("telegram_bot.services.requests.post")
    def test_send_telegram_message(self, mock_post):
        """Тестирование успешного запроса к Telegram API."""
        mock_response = Mock()
        mock_response.json.return_value = {"ok": True}
        mock_post.return_value = mock_response

        result = send_telegram_message(123456789, "Тестовое сообщение")

        self.assertEqual(result, {"ok": True})
        mock_post.assert_called_once_with(
            "https://api.telegram.org/bottest-token/sendMessage",
            json={"chat_id": 123456789, "text": "Тестовое сообщение"},
            timeout=10,
        )
        mock_response.raise_for_status.assert_called_once_with()

    @patch("telegram_bot.services.requests.post")
    def test_send_telegram_message_raises_api_error(self, mock_post):
        """Тестирование передачи ошибки Telegram API."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = RequestException("API error")
        mock_post.return_value = mock_response

        with self.assertRaises(RequestException):
            send_telegram_message(123456789, "Тестовое сообщение")


class TelegramTaskTestCase(TestCase):
    def setUp(self):
        super().setUp()
        self.now = datetime(
            2026,
            8,
            24,
            10,
            30,
            tzinfo=ZoneInfo("Europe/Moscow"),
        )
        self.user = User.objects.create_user(
            email="user@example.com",
            password="TestPassword123!",
            telegram_chat_id=123456789,
        )
        self.pleasant_habit = Habit.objects.create(
            owner=self.user,
            place="Ванная",
            time=time(21, 0),
            action="Принять ванну",
            is_pleasant=True,
            duration=120,
        )

    def create_habit(self, **kwargs):
        """Создаёт привычку для проверки Telegram-задач."""
        data = {
            "owner": self.user,
            "place": "Дом",
            "time": time(10, 30),
            "action": "Сделать зарядку",
            "frequency": 1,
            "reward": "Выпить кофе",
            "duration": 60,
        }
        data.update(kwargs)
        return Habit.objects.create(**data)

    def localtime(self, value=None):
        """Возвращает фиксированное время для Celery-задачи."""
        return self.now if value is None else value

    def test_build_habit_message_with_reward(self):
        """Тестирование текста напоминания с вознаграждением."""
        habit = self.create_habit()

        message = build_habit_message(habit)

        self.assertIn("Действие: Сделать зарядку", message)
        self.assertIn("Место: Дом", message)
        self.assertIn("Время: 10:30", message)
        self.assertIn("Время на выполнение: 60 сек.", message)
        self.assertIn("Вознаграждение: Выпить кофе", message)

    def test_build_habit_message_with_related_habit(self):
        """Тестирование текста напоминания со связанной привычкой."""
        habit = self.create_habit(
            reward="",
            related_habit=self.pleasant_habit,
        )

        message = build_habit_message(habit)

        self.assertIn("После выполнения: Принять ванну", message)
        self.assertNotIn("Вознаграждение:", message)

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_send_habit_reminder(self, mock_localtime, mock_send):
        """Тестирование отправки первого напоминания."""
        mock_localtime.side_effect = self.localtime
        habit = self.create_habit()

        result = send_habit_reminders()

        self.assertEqual(result, 1)
        mock_send.assert_called_once()
        habit.refresh_from_db()
        self.assertEqual(habit.last_notification_at, self.now)

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_skip_habit_before_frequency(self, mock_localtime, mock_send):
        """Тестирование пропуска привычки до наступления периодичности."""
        mock_localtime.side_effect = self.localtime
        habit = self.create_habit(
            frequency=3,
            last_notification_at=self.now - timedelta(days=2),
        )

        result = send_habit_reminders()

        self.assertEqual(result, 0)
        mock_send.assert_not_called()
        habit.refresh_from_db()
        self.assertEqual(
            habit.last_notification_at,
            self.now - timedelta(days=2),
        )

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_send_habit_after_frequency(self, mock_localtime, mock_send):
        """Тестирование повторной отправки после периода ожидания."""
        mock_localtime.side_effect = self.localtime
        habit = self.create_habit(
            frequency=3,
            last_notification_at=self.now - timedelta(days=3),
        )

        result = send_habit_reminders()

        self.assertEqual(result, 1)
        mock_send.assert_called_once()
        habit.refresh_from_db()
        self.assertEqual(habit.last_notification_at, self.now)

    @patch("telegram_bot.tasks.send_telegram_message")
    @patch("telegram_bot.tasks.timezone.localtime")
    def test_failed_message_does_not_update_habit(self, mock_localtime, mock_send):
        """Тестирование сохранения статуса при ошибке Telegram."""
        mock_localtime.side_effect = self.localtime
        mock_send.side_effect = RequestException("API error")
        habit = self.create_habit()

        with self.assertRaises(RequestException):
            send_habit_reminders()

        habit.refresh_from_db()
        self.assertIsNone(habit.last_notification_at)

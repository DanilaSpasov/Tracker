from datetime import time

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from habits.models import Habit
from users.models import User


class HabitAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.user = User.objects.create_user(
            email="user@example.com",
            password="TestPassword123!",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="TestPassword123!",
        )
        self.client.force_authenticate(user=self.user)
        self.list_url = reverse("habits-list")
        self.public_url = reverse("public-habits")
        self.valid_data = {
            "place": "Дом",
            "time": "08:00:00",
            "action": "Сделать зарядку",
            "is_pleasant": False,
            "frequency": 1,
            "reward": "Выпить кофе",
            "duration": 60,
            "is_public": False,
        }

    def create_habit(self, owner=None, **kwargs):
        """Создаёт привычку с корректными значениями по умолчанию."""
        data = {
            "owner": owner or self.user,
            "place": "Дом",
            "time": time(8, 0),
            "action": "Сделать зарядку",
            "frequency": 1,
            "duration": 60,
        }
        data.update(kwargs)
        return Habit.objects.create(**data)

    def test_create_habit(self):
        """Тестирование создания привычки текущим пользователем."""
        response = self.client.post(self.list_url, self.valid_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        habit = Habit.objects.get(id=response.data["id"])
        self.assertEqual(habit.owner, self.user)
        self.assertEqual(habit.action, "Сделать зарядку")

    def test_get_only_own_habits(self):
        """Тестирование получения только собственных привычек."""
        own_habit = self.create_habit()
        self.create_habit(owner=self.other_user, action="Чужая привычка")

        response = self.client.get(self.list_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], own_habit.id)

    def test_habits_pagination(self):
        """Тестирование пагинации по пять привычек."""
        for number in range(6):
            self.create_habit(action=f"Привычка {number}")

        first_page = self.client.get(self.list_url)
        second_page = self.client.get(self.list_url, {"limit": 5, "offset": 5})

        self.assertEqual(first_page.data["count"], 6)
        self.assertEqual(len(first_page.data["results"]), 5)
        self.assertIsNotNone(first_page.data["next"])
        self.assertEqual(len(second_page.data["results"]), 1)

    def test_retrieve_update_and_delete_own_habit(self):
        """Тестирование просмотра, изменения и удаления своей привычки."""
        habit = self.create_habit()
        detail_url = reverse("habits-detail", args=[habit.id])

        retrieve_response = self.client.get(detail_url)
        update_response = self.client.patch(
            detail_url,
            {"action": "Выполнить растяжку"},
            format="json",
        )
        delete_response = self.client.delete(detail_url)

        self.assertEqual(retrieve_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data["action"], "Выполнить растяжку")
        self.assertEqual(delete_response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Habit.objects.filter(id=habit.id).exists())

    def test_cannot_access_other_users_habit(self):
        """Тестирование недоступности чужой привычки по идентификатору."""
        habit = self.create_habit(owner=self.other_user)
        detail_url = reverse("habits-detail", args=[habit.id])

        get_response = self.client.get(detail_url)
        patch_response = self.client.patch(
            detail_url,
            {"action": "Изменить чужую привычку"},
            format="json",
        )
        delete_response = self.client.delete(detail_url)

        self.assertEqual(get_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(patch_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_public_habits_without_authentication(self):
        """Тестирование публичного списка без авторизации."""
        public_habit = self.create_habit(is_public=True)
        self.create_habit(is_public=False, action="Непубличная привычка")
        self.client.force_authenticate(user=None)

        response = self.client.get(self.public_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["count"], 1)
        self.assertEqual(response.data["results"][0]["id"], public_habit.id)

    def test_reward_and_related_habit_are_mutually_exclusive(self):
        """Тестирование запрета двух видов вознаграждения одновременно."""
        pleasant_habit = self.create_habit(
            action="Принять ванну",
            is_pleasant=True,
        )
        data = self.valid_data | {"related_habit": pleasant_habit.id}

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Нельзя одновременно указывать вознаграждение",
            response.data["non_field_errors"][0],
        )

    def test_duration_cannot_exceed_120_seconds(self):
        """Тестирование максимального времени выполнения."""
        data = self.valid_data | {"duration": 121}

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("duration", response.data)

    def test_frequency_must_be_between_one_and_seven(self):
        """Тестирование допустимой периодичности привычки."""
        for frequency in (0, 8):
            with self.subTest(frequency=frequency):
                data = self.valid_data | {"frequency": frequency}

                response = self.client.post(self.list_url, data, format="json")

                self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
                self.assertIn("frequency", response.data)

    def test_related_habit_must_be_pleasant(self):
        """Тестирование признака приятной связанной привычки."""
        useful_habit = self.create_habit(action="Полезная привычка")
        data = self.valid_data | {
            "reward": "",
            "related_habit": useful_habit.id,
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "Связанной может быть только приятная привычка",
            response.data["non_field_errors"][0],
        )

    def test_pleasant_habit_cannot_have_reward(self):
        """Тестирование запрета вознаграждения у приятной привычки."""
        data = self.valid_data | {"is_pleasant": True}

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "У приятной привычки не может быть вознаграждения",
            response.data["non_field_errors"][0],
        )

    def test_cannot_use_other_users_related_habit(self):
        """Тестирование запрета связывания с чужой привычкой."""
        pleasant_habit = self.create_habit(
            owner=self.other_user,
            action="Чужая приятная привычка",
            is_pleasant=True,
        )
        data = self.valid_data | {
            "reward": "",
            "related_habit": pleasant_habit.id,
        }

        response = self.client.post(self.list_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("related_habit", response.data)

    def test_partial_update_validates_existing_reward(self):
        """Тестирование валидации полей экземпляра при PATCH-запросе."""
        habit = self.create_habit(reward="Выпить кофе")
        detail_url = reverse("habits-detail", args=[habit.id])

        response = self.client.patch(
            detail_url,
            {"is_pleasant": True},
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn(
            "У приятной привычки не может быть вознаграждения",
            response.data["non_field_errors"][0],
        )

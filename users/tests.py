from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from users.models import User


class UserManagerTestCase(TestCase):
    def test_create_user(self):
        """Тестирование создания обычного пользователя."""
        user = User.objects.create_user(
            email="user@EXAMPLE.COM",
            password="TestPassword123!",
        )

        self.assertEqual(user.email, "user@example.com")
        self.assertTrue(user.check_password("TestPassword123!"))
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_user_without_email(self):
        """Тестирование запрета создания пользователя без email."""
        with self.assertRaisesMessage(ValueError, "Email обязателен"):
            User.objects.create_user(email="", password="TestPassword123!")

    def test_create_superuser(self):
        """Тестирование создания суперпользователя."""
        user = User.objects.create_superuser(
            email="admin@example.com",
            password="TestPassword123!",
        )

        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_email_verified)
        self.assertFalse(user.is_blocked)


class UserAPITestCase(APITestCase):
    def setUp(self):
        super().setUp()
        self.password = "TestPassword123!"
        self.register_url = reverse("user_register")
        self.token_url = reverse("token_obtain_pair")
        self.refresh_url = reverse("token_refresh")

    def test_register_user(self):
        """Тестирование регистрации пользователя."""
        data = {
            "email": "user@example.com",
            "password": self.password,
            "telegram_chat_id": 123456789,
        }

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn("password", response.data)
        user = User.objects.get(email="user@example.com")
        self.assertTrue(user.check_password(self.password))
        self.assertEqual(user.telegram_chat_id, 123456789)

    def test_obtain_and_refresh_token(self):
        """Тестирование получения и обновления JWT-токена."""
        User.objects.create_user(
            email="user@example.com",
            password=self.password,
        )

        token_response = self.client.post(
            self.token_url,
            {"email": "user@example.com", "password": self.password},
            format="json",
        )

        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", token_response.data)
        self.assertIn("refresh", token_response.data)

        refresh_response = self.client.post(
            self.refresh_url,
            {"refresh": token_response.data["refresh"]},
            format="json",
        )

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

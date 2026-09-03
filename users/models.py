from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


class UserManager(BaseUserManager):
    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", False)
        extra_fields.setdefault("is_blocked", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_email_verified", True)
        extra_fields.setdefault("is_blocked", False)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Суперпользователь должен иметь is_staff=True")

        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Суперпользователь должен иметь is_superuser=True")

        if extra_fields.get("is_active") is not True:
            raise ValueError("Суперпользователь должен иметь is_active=True")

        if extra_fields.get("is_email_verified") is not True:
            raise ValueError("Email суперпользователя должен быть подтверждён")

        if extra_fields.get("is_blocked") is not False:
            raise ValueError("Суперпользователь не может быть заблокирован")

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    objects = UserManager()
    username = None
    email = models.EmailField(unique=True, verbose_name="Email")
    is_email_verified = models.BooleanField(
        default=False,
        verbose_name="Email подтверждён",
    )
    is_blocked = models.BooleanField(default=False, verbose_name="Заблокирован")
    telegram_chat_id = models.BigIntegerField(
        null=True,
        blank=True,
        unique=True,
        verbose_name="ID чата Telegram",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

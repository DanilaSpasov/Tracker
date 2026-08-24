from django.conf import settings
from django.db import models


class Habit(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="habits",
        verbose_name="Пользователь",
    )
    place = models.CharField(max_length=255, verbose_name="Место")
    time = models.TimeField(verbose_name="Время")
    action = models.CharField(max_length=255, verbose_name="Действие")
    is_pleasant = models.BooleanField(
        default=False,
        verbose_name="Признак приятной привычки",
    )
    related_habit = models.ForeignKey(
        "self",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="useful_habits",
        verbose_name="Связанная привычка",
    )
    frequency = models.PositiveIntegerField(
        default=1,
        verbose_name="Периодичность",
    )
    reward = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="Вознаграждение",
    )
    duration = models.PositiveIntegerField(verbose_name="Время на выполнение")
    is_public = models.BooleanField(
        default=False,
        verbose_name="Признак публичности",
    )

    def __str__(self):
        return f"{self.action} {self.time} {self.place}"

    class Meta:
        verbose_name = "Привычка"
        verbose_name_plural = "Привычки"

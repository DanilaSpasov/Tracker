from celery import shared_task
from django.utils import timezone

from habits.models import Habit
from telegram_bot.services import send_telegram_message


@shared_task
def send_telegram_message_task(chat_id, text):
    return send_telegram_message(chat_id, text)


def build_habit_message(habit):
    message = (
        "Напоминание о привычке!\n"
        f"Действие: {habit.action}\n"
        f"Место: {habit.place}\n"
        f"Время: {habit.time.strftime('%H:%M')}\n"
        f"Время на выполнение: {habit.duration} сек."
    )

    if habit.reward:
        message += f"\nВознаграждение: {habit.reward}"
    elif habit.related_habit:
        message += f"\nПосле выполнения: {habit.related_habit.action}"

    return message


@shared_task
def send_habit_reminders():
    now = timezone.localtime()
    habits = Habit.objects.select_related("owner", "related_habit").filter(
        time__hour=now.hour,
        time__minute=now.minute,
        owner__telegram_chat_id__isnull=False,
    )

    sent_count = 0

    for habit in habits:
        if habit.last_notification_at:
            last_notification = timezone.localtime(habit.last_notification_at)
            days_since_notification = (now.date() - last_notification.date()).days

            if days_since_notification < habit.frequency:
                continue

        send_telegram_message(
            chat_id=habit.owner.telegram_chat_id,
            text=build_habit_message(habit),
        )
        habit.last_notification_at = now
        habit.save(update_fields=["last_notification_at"])
        sent_count += 1

    return sent_count

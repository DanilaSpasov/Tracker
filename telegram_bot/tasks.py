from celery import shared_task

from telegram_bot.services import send_telegram_message


@shared_task
def send_telegram_message_task(chat_id, text):
    return send_telegram_message(chat_id, text)

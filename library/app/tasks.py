from celery import shared_task
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
import logging

logger = logging.getLogger(__name__)

@shared_task
def send_approval_notification(book_title, user_email, first_name, last_name):
    try:
        if first_name and last_name:
            greeting = f'{first_name} {last_name}'
        elif first_name:
            greeting = first_name
        else:
            greeting = 'Уважаемый читатель'
            
        subject = f'Книга "{book_title}" одобрена'
        message = f'''
Здравствуйте, {greeting}!

Ваша книга "{book_title}" была одобрена библиотекарем.

С уважением,
Команда библиотеки
'''
        send_mail(
            subject,
            message.strip(),
            'noreply@library.com',
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Approval notification sent to {user_email} for book '{book_title}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send approval notification: {e}")
        return False

@shared_task
def send_return_reminder(book_title, user_email, first_name, last_name, approval_date):
    try:
        if first_name and last_name:
            greeting = f'{first_name} {last_name}'
        elif first_name:
            greeting = first_name
        else:
            greeting = 'Уважаемый читатель'
            
        subject = f'Напоминание о возврате книги "{book_title}"'
        message = f'''
Здравствуйте, {greeting}!

Напоминаем, что книга "{book_title}" должна быть возвращена в библиотеку 
в течение недели с момента получения ({approval_date.strftime("%d.%m.%Y")}).

Пожалуйста, не забудьте вернуть книгу вовремя.

С уважением,
Команда библиотеки
'''
        send_mail(
            subject,
            message.strip(),
            'noreply@library.com',
            [user_email],
            fail_silently=False,
        )
        logger.info(f"Return reminder sent to {user_email} for book '{book_title}'")
        return True
    except Exception as e:
        logger.error(f"Failed to send return reminder: {e}")
        return False

@shared_task
def schedule_return_reminder(book_title, user_email, first_name, last_name):
    from celery import current_app
    
    reminder_eta = timezone.now() + timedelta(days=7)
    
    send_return_reminder.apply_async(
        args=[book_title, user_email, first_name, last_name, timezone.now()],
        eta=reminder_eta
    )
    
    logger.info(f"Scheduled return reminder for {user_email} in 7 days")
    return f"Reminder scheduled for {reminder_eta}"

@shared_task
def send_approval_and_schedule_reminder(book_title, user_id):
    try:
        user = User.objects.get(id=user_id)
        
        send_approval_notification.delay(
            book_title,
            user.email,
            user.first_name,
            user.last_name
        )
        
        schedule_return_reminder.delay(
            book_title,
            user.email,
            user.first_name,
            user.last_name
        )
        
        logger.info(f"Approval and reminder scheduled for user {user_id}")
        return True
        
    except User.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return False
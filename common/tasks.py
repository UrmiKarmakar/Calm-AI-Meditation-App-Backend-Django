from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

@shared_task
def send_verification_email(email, code):
    """
    Async task to send verification OTP email.
    """
    subject = "Your CalmAI Verification Code"
    message = f"Your OTP code is {code}. It expires in 60 seconds."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [email])

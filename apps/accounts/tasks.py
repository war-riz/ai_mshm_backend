"""
apps/accounts/tasks.py
───────────────────────
Celery tasks for async email delivery.
"""
import logging
import resend

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string

logger = logging.getLogger(__name__)

IS_PRODUCTION = getattr(settings, "DJANGO_ENV", "development") == "production"


def _send_email(to: str, subject: str, html_message: str, plain_message: str = ""):
    """Route email through Resend (production) or SMTP (development)."""
    if IS_PRODUCTION:
        resend.api_key = settings.RESEND_API_KEY
        resend.Emails.send({
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": to,
            "subject": subject,
            "html": html_message,
        })
    else:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to],
            fail_silently=False,
        )


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    name="accounts.send_verification_email",
)
def send_verification_email_task(self, user_id: str, user_name: str, user_email: str, verify_url: str):
    """Send email verification link."""
    html_message = render_to_string(
        "emails/verify_email.html",
        {"user_name": user_name, "verify_url": verify_url, "app_name": settings.APP_NAME},
    )
    plain_message = (
        f"Hi {user_name},\n\n"
        f"Please verify your email by visiting:\n{verify_url}\n\n"
        f"This link expires in {settings.EMAIL_VERIFICATION_EXPIRY_HOURS} hours.\n\n"
        f"— The {settings.APP_NAME} Team"
    )
    _send_email(
        to=user_email,
        subject=f"Verify your {settings.APP_NAME} email",
        html_message=html_message,
        plain_message=plain_message,
    )
    logger.info("Verification email sent to %s", user_email)


@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    max_retries=3,
    name="accounts.send_password_reset_email",
)
def send_password_reset_email_task(self, user_name: str, user_email: str, reset_url: str):
    """Send password reset link."""
    html_message = render_to_string(
        "emails/reset_password.html",
        {"user_name": user_name, "reset_url": reset_url, "app_name": settings.APP_NAME},
    )
    plain_message = (
        f"Hi {user_name},\n\n"
        f"Reset your password here:\n{reset_url}\n\n"
        f"This link expires in {settings.PASSWORD_RESET_EXPIRY_HOURS} hours.\n"
        f"If you didn't request this, please ignore this email.\n\n"
        f"— The {settings.APP_NAME} Team"
    )
    _send_email(
        to=user_email,
        subject=f"Reset your {settings.APP_NAME} password",
        html_message=html_message,
        plain_message=plain_message,
    )
    logger.info("Password reset email sent to %s", user_email)
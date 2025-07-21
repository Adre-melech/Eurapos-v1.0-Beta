from django.core.mail import send_mail
from django.conf import settings
from adminpanel.models import AdminNotification


def notify_admin(message: str, type: str = "contact_form", email: bool = True):
    """
    Creates an admin notification entry and optionally sends an email alert.

    Args:
        message (str): The content of the notification.
        type (str): One of AdminNotification.TYPE_CHOICES (default: 'contact_form').
        email (bool): Whether to send an email alert.
    """
    # Save in adminpanel DB
    AdminNotification.objects.create(message=message, type=type)

    # Send email if enabled
    if email:
        subject_type = type.replace("_", " ").title()
        send_mail(
            subject=f"📢 Admin Alert: {subject_type}",
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=True
        )
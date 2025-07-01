from django.utils.timezone import now
from notifications.models import Notification


def notify_expiration(seeker):
    Notification.objects.create(
        seeker=seeker,
        message="⏳ Your exclusive job access has expired. Unlock again anytime!"
    )
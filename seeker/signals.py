import logging
from datetime import timedelta
from django.conf import settings
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.dispatch import receiver
from django.utils.timezone import now
from seeker.models import UserActivity, SuspiciousLoginAlert

logger = logging.getLogger(__name__)

@receiver(user_logged_in)
def stitch_user_activity(sender, request, user, **kwargs):
    """
    When a user logs in, stitch their anonymous session activity to their account.
    If suspicious behavior occurred before login, log it and alert admins.
    """
    session_key = request.session.session_key
    if not session_key:
        return

    # Stitch anonymous activity to the logged-in user
    UserActivity.objects.filter(
        session_key=session_key,
        user__isnull=True
    ).update(
        user=user,
        is_authenticated=True
    )

    # Detect suspicious activity in the last 10 minutes
    suspicious_count = UserActivity.objects.filter(
        session_key=session_key,
        is_suspicious=True,
        timestamp__gte=now() - timedelta(minutes=10)
    ).count()

    # Calculate behavior score
    behavior_score = calculate_behavior_score(session_key)

    if suspicious_count > 0:
        logger.warning(f"[⚠️] Suspicious login detected for {user.username}: {suspicious_count} events")

        # Send email alert
        send_mail(
            subject=f"⚠️ Suspicious Login: {user.username}",
            message=(
                f"{suspicious_count} suspicious actions were detected before login.\n"
                f"Behavior Score: {behavior_score}\n"
                f"IP: {request.META.get('REMOTE_ADDR')}\n"
                f"User Agent: {request.META.get('HTTP_USER_AGENT')}"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[settings.ADMIN_NOTIFICATION_EMAIL],
            fail_silently=True
        )

        # Log alert in admin
        SuspiciousLoginAlert.objects.create(
            user=user,
            session_key=session_key,
            suspicious_count=suspicious_count,
            behavior_score=behavior_score,
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT")
        )


def calculate_behavior_score(session_key):
    """
    Calculates a behavior score based on session activity.
    Higher scores indicate potentially suspicious or aggressive behavior.
    """
    activities = UserActivity.objects.filter(session_key=session_key)
    score = 0

    for activity in activities:
        if activity.is_suspicious:
            score += 10
        if "/resume/" in activity.path or "/unlock/" in activity.path:
            score += 5
        if activity.method == "POST":
            score += 3

    return score
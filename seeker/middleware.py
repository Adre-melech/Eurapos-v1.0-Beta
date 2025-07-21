from seeker.models import UserActivity
from django.utils.timezone import now
from datetime import timedelta


class ActivityLoggerMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Skip logging for admin/staff users
        if request.user.is_authenticated and request.user.is_staff:
            return response

        # Ensure session exists
        if not request.session.session_key:
            request.session.save()

        session_key = request.session.session_key
        user_agent = request.META.get("HTTP_USER_AGENT", "").lower()
        ip_address = request.META.get("REMOTE_ADDR")
        path = request.path
        method = request.method
        referrer = request.META.get("HTTP_REFERER")

        # Detect suspicious behavior
        recent_views = UserActivity.objects.filter(
            session_key=session_key,
            timestamp__gte=now() - timedelta(minutes=5)
        ).count()

        is_bot = any(bot in user_agent for bot in ["curl", "bot", "scrapy", "python-requests"])
        is_suspicious = recent_views > 50 or is_bot

        # Log activity
        UserActivity.objects.create(
            user=request.user if request.user.is_authenticated else None,
            session_key=session_key,
            is_authenticated=request.user.is_authenticated,
            path=path,
            method=method,
            ip_address=ip_address,
            user_agent=user_agent,
            referrer=referrer,
            is_suspicious=is_suspicious
        )

        return response
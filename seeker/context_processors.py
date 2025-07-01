from notifications.models import Notification

def seeker_notifications(request):
    if request.user.is_authenticated:
        seeker = request.user
        notifications = Notification.objects.filter(seeker=seeker).order_by("-created_at")
        return {
            "recent_notifications": notifications[:10],
            "unread_notifications": notifications.filter(read=False)
        }
    return {}
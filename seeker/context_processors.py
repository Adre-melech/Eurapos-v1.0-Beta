from notifications.models import Notification
from jobs.models import UnlockedExclusiveJob

def seeker_notifications(request):
    if request.user.is_authenticated:
        seeker = request.user
        notifications = Notification.objects.filter(seeker=seeker).order_by("-created_at")
        return {
            "recent_notifications": notifications[:10],
            "unread_notifications": notifications.filter(read=False)
        }
    return {}


def unlocked_jobs_processor(request):
    if request.user.is_authenticated:
        return {
            'unlocked_jobs': UnlockedExclusiveJob.objects.filter(seeker=request.user).exists()
        }
    return {'unlocked_jobs': False}

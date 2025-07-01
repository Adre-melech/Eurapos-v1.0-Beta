from django.utils.timezone import now
from jobs.models import UnlockedExclusiveJob

def unlocked_jobs_status(request):
    if request.user.is_authenticated:
        unlocked = UnlockedExclusiveJob.objects.filter(
            seeker=request.user,
            active=True,
            expires_at__gte=now()
        ).exists()
        return {'unlocked_jobs': unlocked}
    return {'unlocked_jobs': False}
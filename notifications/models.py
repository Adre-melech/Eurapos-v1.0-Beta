from django.db import models
from seeker.models import Seeker

class Notification(models.Model):
    """Stores all in-app notifications triggered by seeker activity."""
    seeker = models.ForeignKey(Seeker, related_name="notifications", on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.seeker.username} - {self.message[:50]}"

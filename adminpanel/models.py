from django.db import models
from django.utils.timezone import now
from seeker.models import Seeker

class AdminNotification(models.Model):
    """Stores in-app admin notifications for various activities."""
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)  # Tracks if notification has been read

    def mark_as_read(self):
        """Marks notification as read."""
        self.read = True
        self.save(update_fields=["read"])

    def __str__(self):
        return f"Admin Notification - {self.created_at} ({'Read' if self.read else 'Unread'})"


class HiddenJobAccess(models.Model):
    """Tracks users who unlocked hidden job listings."""
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)  # Tracks if access is still valid

    def deactivate(self):
        """Marks Hidden Job Access as inactive once expired."""
        if self.expires_at < now():
            self.active = False
            self.save(update_fields=["active"])

    def __str__(self):
        return f"Hidden Job Access - {self.seeker.username} ({'Active' if self.active else 'Expired'})"


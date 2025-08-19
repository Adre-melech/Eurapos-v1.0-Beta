from django.db import models
from django.utils.timezone import now
from seeker.models import Seeker


class AdminNotification(models.Model):
    """Stores in-app admin notifications for various platform events."""

    TYPE_CHOICES = [
        ("job_application", "New Job Application"),
        ("priority_application", "Priority Application"),
        ("whatsapp_job", "WhatsApp Job Alert"),
        ("ats_cv_request", "ATS CV Request"),
        ("event_ticket", "Event Ticket Bought"),
        ("visa_guide", "Visa Guide Sold"),
        ("contact_form", "Contact Form Submission"),
    ]

    message = models.TextField()
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default="contact_form")
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    def mark_as_read(self):
        """Marks notification as read."""
        self.read = True
        self.save(update_fields=["read"])

    def __str__(self):
        status = "âœ… Read" if self.read else "ðŸ”” Unread"
        label = dict(self.TYPE_CHOICES).get(self.type, "Unknown")
        return f"[{label}] {self.created_at.strftime('%Y-%m-%d %H:%M')} â€” {status}"


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



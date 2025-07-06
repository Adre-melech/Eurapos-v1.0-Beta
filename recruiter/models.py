from django.db import models


class PartnerRegistration(models.Model):
    company = models.CharField(max_length=200)
    email = models.EmailField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    # ✅ Admin-only controls
    is_approved = models.BooleanField(default=False)
    staff_notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("company", "email")  # prevent dupes

    def __str__(self):
        return f"{self.company} ({self.email})"
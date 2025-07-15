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


class ResumeAccessOrder(models.Model):
    PLAN_CHOICES = [
        ("starter", "Starter"),
        ("professional", "Professional"),
        ("enterprise", "Enterprise"),
    ]

    plan = models.CharField(max_length=20, choices=PLAN_CHOICES)
    company_name = models.CharField(max_length=100, blank=True)
    name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)
    contacted = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.get_plan_display()}) – {self.email}"
from django.db import models

class ContactMessage(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    responded = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.email})"


class PolicySection(models.Model):
    POLICY_CHOICES = [
        ("terms", "Terms & Conditions"),
        ("privacy", "Privacy Policy"),
    ]

    policy_type = models.CharField(max_length=20, choices=POLICY_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    updated_at = models.DateField(auto_now=True)

    def __str__(self):
        return f"[{self.get_policy_type_display()}] {self.title}"

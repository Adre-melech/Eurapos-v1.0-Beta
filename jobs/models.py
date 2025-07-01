from django.core.mail import send_mail
from django.db import models
from datetime import timedelta
from django.utils.timezone import now
from adminpanel.models import AdminNotification
from django.apps import apps  # Helps prevent circular imports

class SeekerCountry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobCountry(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class JobTitle(models.Model):
    name = models.CharField(max_length=255)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)  # Ensures foreign key exists

    def __str__(self):
        return self.name


class JobPost(models.Model):
    job_id = models.CharField(max_length=10, unique=True, blank=True)
    title = models.CharField(max_length=200)
    company_name = models.CharField(max_length=200)
    salary = models.CharField(max_length=100)
    deadline = models.DateField()
    description = models.TextField()
    required_skills = models.TextField()

    country = models.ForeignKey(JobCountry, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)

    exclusive_job = models.BooleanField(default=False)  # Marks hidden jobs
    views = models.PositiveIntegerField(default=0)

    # ✅ Added `created_at` field to track recent jobs
    created_at = models.DateTimeField(auto_now_add=True)

    # HR Contact Info
    hr_name = models.CharField(max_length=100)
    hr_phone = models.CharField(max_length=20)
    hr_email = models.EmailField()

    def save(self, *args, **kwargs):
        """Automatically assigns job_id if not provided."""
        if not self.job_id:
            last_job = JobPost.objects.order_by('-id').first()
            new_id = f"JB{str(last_job.id + 1).zfill(3)}" if last_job else "JB001"
            self.job_id = new_id
        super().save(*args, **kwargs)

    def increment_views(self):
        """Increment job views when accessed."""
        self.views += 1
        self.save(update_fields=["views"])

    def __str__(self):
        return f"{self.job_id} - {self.title}"



class UnlockedExclusiveJob(models.Model):
    seeker = models.ForeignKey("seeker.Seeker", on_delete=models.CASCADE)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    active = models.BooleanField(default=True)  # Tracks if the access is still valid

    def unlock_jobs(self, seeker):
        """Unlocks all exclusive jobs for 3 days if seeker has enough credits."""
        if seeker.credits >= 10:
            seeker.credits -= 10
            seeker.save(update_fields=["credits"])
            self.expires_at = now() + timedelta(days=3)
            self.save(update_fields=["expires_at", "active"])


class Application(models.Model):
    STATUS_CHOICES = [
        ("Submitted", "Submitted"),
        ("Under Review", "Under Review"),
        ("Selected", "Selected"),
        ("Rejected", "Rejected"),
    ]

    RATING_CHOICES = [
        ("good", "🙂 Good"),
        ("okay", "😐 Okay"),
        ("bad", "☹️ Bad"),
    ]

    seeker = models.ForeignKey("seeker.Seeker", on_delete=models.CASCADE)
    job = models.ForeignKey(JobPost, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Submitted")
    cv = models.FileField(upload_to="cv_uploads/", blank=True, null=True)  # Allows CV to be optional
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    rating = models.CharField(max_length=10, choices=RATING_CHOICES, blank=True, null=True)  # Emoji rating

    hr_unlocked = models.BooleanField(default=False)  # Tracks if HR contact is revealed
    rating_credited = models.BooleanField(default=False)  # Tracks if credits were awarded for rating

    priority_review = models.BooleanField(default=False)  # Marks priority applications
    purchased_priority_at = models.DateTimeField(blank=True, null=True)  # Tracks purchase time

    def __str__(self):
        return f"Application - {self.seeker.username} for {self.job.title} ({self.status})"

    def unlock_hr_info(self):
        """Unlocks HR contact details for the user."""
        self.hr_unlocked = True
        self.save(update_fields=["hr_unlocked"])

    def award_rating_credits(self):
        """Awards 5 credits when a rating is submitted for the application."""
        if self.rating and not self.rating_credited:
            self.seeker.credits += 5  # Add credits to user
            self.seeker.save(update_fields=["credits"])
            self.rating_credited = True  # Prevent duplicate credit awarding
            self.save(update_fields=["rating_credited"])

    def enable_priority_review(self):
        """Allows user to purchase Priority HR Review and notifies admin."""
        if not self.priority_review and self.seeker.credits >= 15:  # Example: Costs 15 credits
            self.seeker.credits -= 15
            self.seeker.save(update_fields=["credits"])
            self.priority_review = True
            self.purchased_priority_at = now()
            self.save(update_fields=["priority_review", "purchased_priority_at"])
            self.notify_admin()

    def notify_admin(self):
        """Sends an email & creates an in-app notification for admin."""
        # Email Notification
        send_mail(
            subject="🚀 Priority HR Review Purchased!",
            message=f"User {self.seeker.username} has purchased Priority Review for {self.job.title}. Please process it immediately.",
            from_email="noreply@eurapos.com",
            recipient_list=["admin@eurapos.com"],
        )

        # In-App Notification
        AdminNotification.objects.create(
            message=f"🚀 User {self.seeker.username} purchased Priority Review for {self.job.title}. Process immediately!"
        )

    def save(self, *args, **kwargs):
        if self.pk:
            from django.db.models import F
            old_status = Application.objects.filter(pk=self.pk).values_list('status', flat=True).first()
            if old_status != self.status and self.status in ["Under Review", "Selected", "Rejected"]:
                from notifications.models import Notification  # Lazy import to avoid circular import
                messages = {
                    "Under Review": f"🕵️‍♂️ Your application for '{self.job.title}' is now under review.",
                    "Selected": f"🎉 Congratulations! You've been selected for '{self.job.title}'!",
                    "Rejected": f"🙁 Your application for '{self.job.title}' was not selected this time."
                }
                Notification.objects.create(
                    seeker=self.seeker,
                    message=messages[self.status]
                )

        super().save(*args, **kwargs)
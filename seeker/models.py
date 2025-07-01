import random, string
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.timezone import now, timedelta
from django.apps import apps  # Prevents circular import issues


class Seeker(AbstractUser):
    seeker_id = models.CharField(max_length=10, unique=True, blank=True)
    referral_id = models.CharField(max_length=8, unique=True, blank=True)
    phone = models.CharField(max_length=15)

    country = models.ForeignKey("jobs.SeekerCountry", on_delete=models.SET_NULL, null=True)
    job_title = models.ForeignKey("jobs.JobTitle", on_delete=models.SET_NULL, null=True)

    credits = models.PositiveIntegerField(default=5)
    last_login_date = models.DateField(null=True, blank=True)

    preferred_categories = models.ManyToManyField("jobs.Category", blank=True, related_name='preferred_seekers')

    # WhatsApp Job Recommendations
    whatsapp_number = models.CharField(max_length=20, blank=True, null=True)
    receive_whatsapp_jobs = models.BooleanField(default=False)
    whatsapp_number = models.CharField(max_length=15, blank=True, null=True)
    whatsapp_optin_started = models.DateTimeField(null=True, blank=True)
    whatsapp_optin_expires = models.DateTimeField(blank=True, null=True)

    # Visa Discount
    visa_discount_redeemed = models.BooleanField(default=False)
    visa_discount_code = models.CharField(max_length=20, blank=True, null=True)

    # Referral
    referred_by = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    # Group Permissions
    groups = models.ManyToManyField("auth.Group", related_name="seeker_users", blank=True)
    user_permissions = models.ManyToManyField("auth.Permission", related_name="seeker_permissions", blank=True)

    def save(self, *args, **kwargs):
        if not self.is_superuser:
            if not self.seeker_id:
                last_seeker = Seeker.objects.filter(is_superuser=False).order_by('-id').first()
                new_id = f"S{str(last_seeker.id + 1).zfill(3)}" if last_seeker else "S001"
                self.seeker_id = new_id
            if not self.referral_id:
                self.referral_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)

    def add_credits(self, amount, reason=None):
        self.credits += amount
        self.save(update_fields=["credits"])

        # ✅ Lazy import and notify if there's a reason
        if reason:
            from notifications.models import Notification
            Notification.objects.create(
                seeker=self,
                message=reason
            )

    def redeem_credits(self, amount):
        if self.credits >= amount:
            self.credits -= amount
            self.save(update_fields=["credits"])
            return True
        return False

    def grant_daily_login_reward(self):
        today = now().date()
        if self.last_login_date != today:
            self.add_credits(5)
            self.last_login_date = today
            self.save(update_fields=["last_login_date", "credits"])

    def award_referral_bonus(self, referrer):
        if referrer:
            referrer.add_credits(50)

            # ✅ Lazy import to avoid circular import error
            from notifications.models import Notification
            Notification.objects.create(
                seeker=referrer,
                message="🎉 Congrats! Someone used your referral code. You've earned 50 bonus credits!"
            )

    def enable_whatsapp_recommendations(self):
        if self.credits >= 20:
            self.credits -= 20
            self.receive_whatsapp_jobs = True
            self.whatsapp_optin_expires = now() + timedelta(days=10)
            self.save(update_fields=["credits", "receive_whatsapp_jobs", "whatsapp_optin_expires"])
            return True
        return False

    # ✅ Can order ATS CV again (after 15 days)
    def ats_cv_order_available(self):
        ATSResumeRequest = apps.get_model('seeker', 'ATSResumeRequest')
        last_order = ATSResumeRequest.objects.filter(seeker=self).order_by('-requested_at').first()
        if last_order:
            days_passed = (now() - last_order.requested_at).days
            return days_passed >= 15, max(0, 15 - days_passed)
        return True, 0

    # ✅ WhatsApp recommendation status (active within 10 days)
    def whatsapp_recommendation_status(self):
        if self.whatsapp_optin_expires:
            remaining = (self.whatsapp_optin_expires - now()).days
            if remaining > 0:
                return True, remaining
        return False, 0


    # ✅ Can unlock exclusive jobs again (after 3 days)
    def can_unlock_exclusive_jobs(self):
        UnlockedExclusiveJob = apps.get_model('jobs', 'UnlockedExclusiveJob')
        last_unlock = UnlockedExclusiveJob.objects.filter(seeker=self).order_by('-unlocked_at').first()

        if last_unlock:
            cooldown_ends = last_unlock.unlocked_at + timedelta(days=3)
            remaining_seconds = max(0, int((cooldown_ends - now()).total_seconds()))
            return remaining_seconds == 0, remaining_seconds, cooldown_ends

        return True, 0, None

    def __str__(self):
        return f"{self.seeker_id} - {self.username} ({self.credits} Credits)"


class ATSResumeRequest(models.Model):
    """Tracks ATS CV purchase requests and delivery"""
    seeker = models.ForeignKey("Seeker", on_delete=models.CASCADE)
    requested_at = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)  # Admin marks as processed
    order_id = models.CharField(max_length=12, unique=True, blank=True)  # Order tracking ID
    cv_file = models.FileField(upload_to="ats_cvs/", blank=True, null=True)  # Final CV uploaded by admin
    updated_at = models.DateTimeField(auto_now=True)

    def generate_order_id(self):
        """Generates a unique order ID"""
        if not self.order_id:
            self.order_id = "ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.save(update_fields=["order_id"])

    def __str__(self):
        return f"Order {self.order_id} - ATS CV for {self.seeker.username}"

    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        if is_update:
            previous = ATSResumeRequest.objects.filter(pk=self.pk).values_list("cv_file", flat=True).first()
            if not previous and self.cv_file:
                from notifications.models import Notification  # Lazy import to avoid circular import
                Notification.objects.create(
                    seeker=self.seeker,
                    message="📄 Your ATS-optimized CV has been delivered! You can now download it from your dashboard."
                )

        super().save(*args, **kwargs)


class VisaDiscount(models.Model):
    """Tracks purchases of 10% visa consultancy discount"""
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    valid_until = models.DateField(null=True, blank=True)  # ✅ New field for 30-day validity
    order_id = models.CharField(max_length=12, unique=True, blank=True)  # Order tracking ID
    coupon_code = models.CharField(max_length=12, unique=True, blank=True)  # Generates coupon code
    pdf_file = models.FileField(upload_to="visa_discount_pdfs/", blank=True, null=True)  # Stores discount PDF

    def generate_coupon_code(self):
        """Generates a unique coupon code"""
        if not self.coupon_code:
            self.coupon_code = "VISA-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.save(update_fields=["coupon_code"])

    def generate_order_id(self):
        """Generates a unique order ID"""
        if not self.order_id:
            self.order_id = "ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.save(update_fields=["order_id"])

    def set_validity_period(self, days=30):
        """Sets the discount validity period"""
        if not self.valid_until:
            self.valid_until = now().date() + timedelta(days=days)
            self.save(update_fields=["valid_until"])

    def __str__(self):
        return f"Order {self.order_id} - Visa Discount ({self.seeker.username})"


class VisaGuide(models.Model):
    """Stores Visa Guidelines uploaded by the admin"""
    country = models.CharField(max_length=100)
    image = models.ImageField(upload_to="visa_guides/")
    pdf_file = models.FileField(upload_to="visa_guides/")
    credits_required = models.PositiveIntegerField(default=20)  # Set cost in credits

    def __str__(self):
        return f"Visa Guide - {self.country} ({self.credits_required} Credits)"


class UnlockedVisaGuide(models.Model):
    """Tracks purchases of Visa Guidelines by users"""
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE)
    guide = models.ForeignKey(VisaGuide, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.seeker.username} unlocked {self.guide.country}"

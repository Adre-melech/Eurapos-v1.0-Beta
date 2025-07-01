from django.db.models.signals import post_save
from django.dispatch import receiver
from seeker.models import Seeker
from notifications.models import Notification
from .models import JobCountry, Category, JobTitle, JobPost


def notify_all_seekers(message):
    for seeker in Seeker.objects.all():
        Notification.objects.create(seeker=seeker, message=message)

@receiver(post_save, sender=JobCountry)
def job_country_created(sender, instance, created, **kwargs):
    if created:
        notify_all_seekers(f"🌍 New job country added: {instance.name}")

@receiver(post_save, sender=Category)
def category_created(sender, instance, created, **kwargs):
    if created:
        notify_all_seekers(f"🧭 New job category: {instance.name}")

@receiver(post_save, sender=JobTitle)
def job_title_created(sender, instance, created, **kwargs):
    if created:
        notify_all_seekers(f"📌 New job title available: {instance.name}")

@receiver(post_save, sender=JobPost)
def job_post_created(sender, instance, created, **kwargs):
    if created and not instance.exclusive_job:
        notify_all_seekers(f"💼 New job posted: {instance.title} at {instance.company_name}")
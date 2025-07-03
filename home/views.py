import random

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.timezone import now
from datetime import timedelta
from jobs.models import JobPost, JobCountry, Category, UnlockedExclusiveJob
from seeker.models import VisaGuide, UnlockedVisaGuide
from events.models import EventTicket


def homepage(request):
    """Displays homepage with personalized and general job listings."""
    jobs = JobPost.objects.filter(exclusive_job=False).order_by("?")[:6]
    categories = Category.objects.all()
    countries = JobCountry.objects.all()
    event_tickets = EventTicket.objects.filter(available_until__gte=now().date()).order_by("available_until")[:4]
    total_events_count = EventTicket.objects.filter(available_until__gte=now().date()).count()
    visa_guides = VisaGuide.objects.order_by("country")[:6]

    unlocked_visa_guides = []
    unlocked_guide_ids = []

    if request.user.is_authenticated:
        unlocked_visa_guides = UnlockedVisaGuide.objects.filter(seeker=request.user)
        unlocked_guide_ids = unlocked_visa_guides.values_list("guide_id", flat=True)

    near_deadline_jobs = JobPost.objects.filter(
        deadline__gte=now(),
        deadline__lte=now() + timedelta(days=10),
        exclusive_job=False
    ).order_by("deadline")[:3]

    hot_jobs = JobPost.objects.filter(
        exclusive_job=False
    ).order_by("-views")[:3]

    latest_jobs = JobPost.objects.filter(
        exclusive_job=False
    ).order_by("-created_at")[:6]

    recommended_jobs = []
    exclusive_jobs = []

    if request.user.is_authenticated:
        seeker = request.user

        # Recommended based on job title category
        if seeker.job_title and seeker.job_title.category:
            recommended_jobs = list(JobPost.objects.filter(
                category=seeker.job_title.category,
                exclusive_job=False
            ).distinct()[:3])

        # Top up with preferred categories if needed
        if len(recommended_jobs) < 3 and seeker.preferred_categories.exists():
            preferred = seeker.preferred_categories.exclude(id=seeker.job_title.category.id)
            more_jobs = JobPost.objects.filter(
                category__in=preferred,
                exclusive_job=False
            ).exclude(id__in=[job.id for job in recommended_jobs])[:3 - len(recommended_jobs)]
            recommended_jobs += list(more_jobs)

        # Exclusive jobs (only those unlocked and not expired)
        unlocked_jobs = UnlockedExclusiveJob.objects.filter(
            seeker=seeker,
            active=True,
            expires_at__gte=now()
        ).values_list("job_id", flat=True)

        exclusive_jobs = JobPost.objects.filter(id__in=unlocked_jobs).order_by("-created_at")[:6]

    context = {
        "jobs": jobs,
        "categories": categories,
        "countries": countries,
        "visa_guides": visa_guides,
        "unlocked_visa_guides": unlocked_visa_guides,
        "unlocked_guide_ids": unlocked_guide_ids,
        "recommended_jobs": recommended_jobs,
        "near_deadline_jobs": near_deadline_jobs,
        "hot_jobs": hot_jobs,
        "latest_jobs": latest_jobs,
        "exclusive_jobs": exclusive_jobs,
        "event_tickets": event_tickets,
        "total_events_count": total_events_count,
    }

    return render(request, "home/index.html", context)



@login_required
def visa_guides_page(request):
    """Displays all visa guides and highlights which ones the seeker has unlocked."""
    seeker = request.user

    visa_guides = VisaGuide.objects.order_by("country")
    unlocked_guide_ids = UnlockedVisaGuide.objects.filter(
        seeker=seeker
    ).values_list("guide_id", flat=True)

    return render(request, "home/visa_guides.html", {
        "visa_guides": visa_guides,
        "unlocked_guide_ids": unlocked_guide_ids,
    })

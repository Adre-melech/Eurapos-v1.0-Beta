import random
import json
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils.timezone import now
from datetime import timedelta
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_http_methods
from .models import ContactMessage, PolicySection
from jobs.models import JobPost, JobCountry, Category, UnlockedExclusiveJob
from seeker.models import VisaGuide, UnlockedVisaGuide, ConsentLog
from events.models import EventTicket


@csrf_exempt
def accept_consent(request):
    if request.method == "POST":
        data = json.loads(request.body)
        tz = data.get("timezone") or "UTC"
        ip = request.META.get("REMOTE_ADDR")

        if request.user.is_authenticated:
            seeker = request.user
            seeker.timezone = tz
            seeker.consent_accepted = True
            seeker.consent_accepted_at = now()
            seeker.save(update_fields=["timezone", "consent_accepted", "consent_accepted_at"])

        ConsentLog.objects.create(
            ip_address=ip,
            timezone=tz
        )

        return JsonResponse({"status": "ok"})




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




def visa_guides_page(request):
    """Displays all visa guides and highlights which ones the seeker has unlocked."""
    visa_guides = VisaGuide.objects.order_by("country")

    unlocked_guide_ids = []
    if request.user.is_authenticated and hasattr(request.user, 'seeker'):
        unlocked_guide_ids = UnlockedVisaGuide.objects.filter(
            seeker=request.user
        ).values_list("guide_id", flat=True)

    return render(request, "home/visa_guides.html", {
        "visa_guides": visa_guides,
        "unlocked_guide_ids": unlocked_guide_ids,
    })


def about_us(request):
    return render(request, "home/about.html")

def contact_us(request):
    return render(request, "home/contact.html")

def rewards(request):
    return render(request, "home/rewards.html")

@require_http_methods(["GET", "POST"])
def send_contact(request):
    if request.method == "POST":
        name = request.POST.get("name")
        email = request.POST.get("email")
        message = request.POST.get("message")

        # Basic validation
        if not name or not email or not message:
            messages.error(request, "⚠️ Please fill out all fields.")
            return redirect("home:send_contact")

        # Save to DB (optional)
        ContactMessage.objects.create(name=name, email=email, message=message)

        # Optional email to admin
        send_mail(
            subject=f"New Contact from {name}",
            message=message,
            from_email=email,
            recipient_list=["support@example.com"],  # update this
            fail_silently=True
        )

        messages.success(request, "✅ Thank you! Your message has been sent.")
        return redirect("home:send_contact")

    return render(request, "home/contact.html")



def faq(request):
    return render(request, "home/faq.html")

@require_GET
def terms_view(request):
    sections = PolicySection.objects.filter(policy_type="terms").order_by("id")
    latest_update = sections.order_by("-updated_at").first()
    return render(request, "home/terms.html", {
        "sections": sections,
        "policy_label": "Terms & Conditions",
        "effective_date": latest_update.updated_at if latest_update else None,
    })

@require_GET
def privacy_view(request):
    sections = PolicySection.objects.filter(policy_type="privacy").order_by("id")
    latest_update = sections.order_by("-updated_at").first()
    return render(request, "home/privacy.html", {
        "sections": sections,
        "policy_label": "Privacy Policy",
        "effective_date": latest_update.updated_at if latest_update else None,
    })




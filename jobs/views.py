from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q
from django_q.tasks import schedule
from django.template.loader import render_to_string
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.utils.timezone import now
from .models import JobPost, JobCountry, Category, UnlockedExclusiveJob
from notifications.models import Notification
from adminpanel.models import HiddenJobAccess
from seeker.models import Seeker
from datetime import timedelta
from django.utils import timezone
from django.contrib import messages
from .models import Application
from .tasks import notify_expiration


def job_list(request):
    """Displays personalized job listings for logged-in seekers & general listings for guests."""
    categories = Category.objects.all()
    countries = JobCountry.objects.all()

    # Base queryset for non-exclusive jobs
    non_exclusive_jobs = JobPost.objects.filter(exclusive_job=False).select_related('category', 'country')

    # Jobs for main section
    jobs = non_exclusive_jobs.order_by("?")[:10]

    # Personalized sections
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

        # 🔐 Exclusive jobs (only if user unlocked them)
        unlocked_jobs = UnlockedExclusiveJob.objects.filter(
            seeker=seeker,
            active=True,
            expires_at__gte=now()
        ).values_list("job_id", flat=True)

        exclusive_jobs = JobPost.objects.filter(id__in=unlocked_jobs).order_by("-created_at")[:3]

    # Other categorized sections
    near_deadline_jobs = non_exclusive_jobs.filter(
        deadline__gte=now(),
        deadline__lte=now() + timedelta(days=10)
    ).order_by("deadline")[:3]

    hot_jobs = non_exclusive_jobs.order_by("-views")[:3]
    latest_jobs = non_exclusive_jobs.order_by("-created_at")[:6]

    # AJAX filtering
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        search_query = request.GET.get("search", "").strip()
        category_id = request.GET.get("category")
        country_id = request.GET.get("country")

        filter_conditions = Q(exclusive_job=False)

        if search_query:
            filter_conditions &= Q(title__icontains=search_query)
        if category_id and category_id.isdigit():
            filter_conditions &= Q(category__id=int(category_id))
        if country_id and country_id.isdigit():
            filter_conditions &= Q(country__id=int(country_id))

        filtered_jobs = JobPost.objects.filter(filter_conditions).select_related('category', 'country')
        html = render_to_string("jobs/partials/job_results.html", {"jobs": filtered_jobs})
        return JsonResponse({"html": html})

    return render(request, "jobs/job_list.html", {
        "jobs": jobs,
        "exclusive_jobs": exclusive_jobs,
        "recommended_jobs": recommended_jobs,
        "near_deadline_jobs": near_deadline_jobs,
        "hot_jobs": hot_jobs,
        "latest_jobs": latest_jobs,
        "categories": categories,
        "countries": countries,
    })



# All Jobs (Random)
# ✅ Display Initial Random Non-Exclusive Jobs
def all_jobs(request):
    """Displays initial 20 random non-exclusive jobs."""
    all_jobs_queryset = JobPost.objects.filter(exclusive_job=False)
    initial_jobs = all_jobs_queryset.order_by("?")[:20]

    categories = Category.objects.all()
    countries = JobCountry.objects.all()

    has_more_jobs = all_jobs_queryset.count() > 20  # ✅ Add this

    return render(request, "jobs/all_jobs.html", {
        "jobs": initial_jobs,
        "categories": categories,
        "countries": countries,
        "has_more_jobs": has_more_jobs  # ✅ Pass to template
    })


# ✅ Load More Jobs with Pagination
def load_more_jobs(request):
    """Loads 10 more random non-exclusive jobs dynamically."""
    exclude_ids = request.GET.get("exclude_ids", "")
    exclude_ids = [int(i) for i in exclude_ids.split(",") if i.isdigit()]

    all_jobs = JobPost.objects.filter(exclusive_job=False).exclude(id__in=exclude_ids)
    new_jobs = all_jobs.order_by("?")[:10]

    jobs_data = [
        {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "salary": job.salary,
            "deadline": job.deadline.strftime("%B %d, %Y"),
            "country": job.country.name,
        }
        for job in new_jobs
    ]

    return JsonResponse({
        "jobs": jobs_data,
        "has_more": all_jobs.count() > 10
    })


def ajax_all_jobs_search(request):
    """AJAX handler for filtering and searching all non-exclusive jobs dynamically."""

    search_query = request.GET.get("search", "").strip()
    category_id = request.GET.get("category")
    country_id = request.GET.get("country")

    jobs = JobPost.objects.filter(exclusive_job=False).order_by("?")

    if search_query:
        jobs = jobs.filter(title__icontains=search_query)

    if category_id and category_id.isdigit():
        jobs = jobs.filter(category__id=int(category_id))

    if country_id and country_id.isdigit():
        jobs = jobs.filter(country__id=int(country_id))

    html = render_to_string("jobs/partials/all_jobs_result.html", {
        "jobs": jobs,
        "no_jobs_found": jobs.count() == 0
    }, request=request)

    return JsonResponse({
        "html": html,
        "message": "No jobs found!" if jobs.count() == 0 else ""
    })



# Near Deadline Jobs
# ✅ Near Deadline Jobs (Initial Load)
def near_deadline_jobs(request):
    """Displays the first 10 jobs closing within the next 10 days, with optimized filtering."""

    # Base queryset for near-deadline, non-exclusive jobs
    base_qs = JobPost.objects.filter(
        deadline__gte=now(),
        deadline__lte=now() + timedelta(days=10),
        exclusive_job=False
    ).order_by("deadline")

    jobs = base_qs[:10]
    total_count = base_qs.count()

    return render(request, "jobs/near_deadline_jobs.html", {
        "near_deadline_jobs": jobs,
        "no_jobs_found": total_count == 0,
        "has_more_jobs": total_count > 10,
        "categories": Category.objects.all(),
        "countries": JobCountry.objects.all(),
    })


# ✅ Load More Near Deadline Jobs (Pagination)
def load_more_near_deadline_jobs(request):
    """Loads additional near deadline jobs dynamically."""
    last_job_id = request.GET.get("last_job_id")

    query = JobPost.objects.filter(
        deadline__gte=now(),
        deadline__lte=now() + timedelta(days=10),
        exclusive_job=False
    ).order_by("deadline")

    # ✅ Exclude jobs already displayed
    if last_job_id and last_job_id.isdigit():
        query = query.filter(id__gt=int(last_job_id))

    jobs = list(query[:10])  # Load next batch of 10 jobs

    jobs_data = [
        {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "salary": job.salary,
            "deadline": job.deadline.strftime("%B %d, %Y"),
            "country": job.country.name,
        }
        for job in jobs
    ]

    return JsonResponse({
        "jobs": jobs_data,
        "has_more_jobs": query.count() > 10  # ✅ Ensure correct "Load More" button behavior
    })



# ✅ HOT Jobs View (Most Viewed Jobs)
# ✅ Initial Load: Display Most Viewed Non-Exclusive Jobs
def hot_jobs(request):
    """Displays the top 20 most viewed non-exclusive jobs, showing 10 initially."""
    base_qs = JobPost.objects.filter(exclusive_job=False).order_by("-views")[:20]  # Limit to top 20 jobs
    jobs = base_qs[:10]  # Show first 10 jobs
    total_count = len(base_qs)  # Ensure only 20 jobs are considered

    return render(request, "jobs/hot_jobs.html", {
        "hot_jobs": jobs,
        "no_jobs_found": total_count == 0,
        "has_more_jobs": total_count > 10,  # Show "Load More" only if more jobs exist
        "categories": Category.objects.all(),
        "countries": JobCountry.objects.all(),
    })


# ✅ Load More Hot Jobs (Pagination)
def load_more_hot_jobs(request):
    """Loads additional hot jobs dynamically from the top 20 most viewed jobs."""
    offset = int(request.GET.get("offset", 10))  # Start loading from index 10

    query = JobPost.objects.filter(exclusive_job=False).order_by("-views")[:20]  # Limit to top 20 jobs

    jobs = list(query[offset:offset + 10])  # Load the next batch of 10 jobs

    jobs_data = [
        {
            "id": job.id,
            "title": job.title,
            "company_name": job.company_name,
            "salary": job.salary,
            "views": job.views,
            "country": job.country.name,
        }
        for job in jobs
    ]

    return JsonResponse({
        "jobs": jobs_data,
        "has_more_jobs": offset + len(jobs) < 20  # ✅ Ensure correct "Load More" button behavior
    })


@login_required
def exclusive_jobs(request):
    """View for authenticated users to see unlocked exclusive jobs."""
    unlocked_job_ids = UnlockedExclusiveJob.objects.filter(
        seeker=request.user,
        active=True,
        expires_at__gte=now()
    ).values_list("job_id", flat=True)

    jobs = JobPost.objects.filter(id__in=unlocked_job_ids).order_by("-created_at")

    return render(request, "jobs/exclusive_jobs.html", {"exclusive_jobs": jobs})




def job_detail(request, job_id):
    """Displays detailed job information & application status, including HR contact unlocking."""

    job = get_object_or_404(JobPost, id=job_id)

    # ✅ Increment job views when accessed
    job.increment_views()

    application_status = False  # Default: User hasn't applied
    application = None

    if request.user.is_authenticated:
        seeker = request.user
        application = Application.objects.filter(seeker=seeker, job=job).first()
        application_status = application is not None  # Check if user has applied

    return render(request, "jobs/job_detail.html", {
        "job": job,
        "application": application,
        "application_status": application_status,
    })


@login_required
def apply_job(request, job_id):
    """Handles job application submission & awards credits."""
    job = get_object_or_404(JobPost, id=job_id)
    seeker = request.user

    # Prevent duplicate applications
    if Application.objects.filter(seeker=seeker, job=job).exists():
        messages.warning(request, "You have already applied for this job.")
        return redirect("jobs:job_detail", job_id=job_id)

    if request.method == "POST":
        cv_file = request.FILES.get("cv")

        if not cv_file:
            messages.error(request, "Please upload a CV to apply.")
            return redirect("jobs:job_detail", job_id=job_id)

        # Create and save the application
        Application.objects.create(
            seeker=seeker,
            job=job,
            cv=cv_file,
            status="Submitted"
        )

        # Award credits
        seeker.credits += 5
        seeker.save()

        messages.success(request, "Application submitted! You earned 5 credits.")
        return redirect("jobs:job_detail", job_id=job_id)

    return redirect("jobs:job_detail", job_id=job_id)


def send_job_alerts():
    """Automatically notifies seekers about new job postings"""
    seekers = Seeker.objects.all()
    new_jobs = JobPost.objects.filter(created_at__gte=timezone.now() - timedelta(days=1))

    for job in new_jobs:
        for seeker in seekers:
            Notification.objects.create(
                seeker=seeker,
                message=f"New Job Alert: {job.title} at {job.company_name} - Apply now!"
            )


def update_application_status(application, new_status):
    """Updates job application status & sends notification"""
    application.status = new_status
    application.save()
    Notification.objects.create(
        seeker=application.seeker,
        message=f"Your application for {application.job.title} is now '{new_status}'."
    )


def rate_application(request, application_id):
    """Handles rating submission and awards 5 credits for rating."""
    application = get_object_or_404(Application, id=application_id)

    if request.method == "POST":
        rating = request.POST.get("rating")
        if rating in ["good", "okay", "bad"]:
            application.rating = rating

            # Award 5 credits if the user hasn't received them yet
            if not application.rating_credited:
                application.award_rating_credits()
                messages.success(request, "Thank you for rating your experience! 🎉 You earned 5 credits.")

            application.save(update_fields=["rating", "rating_credited"])
        else:
            messages.error(request, "Invalid rating selection.")

    return redirect("seeker:dashboard")


def ajax_search(request):
    """Handles AJAX-based search & filtering"""
    search_query = request.GET.get("search", "")
    category_id = request.GET.get("category", "")
    country_id = request.GET.get("country", "")

    jobs = JobPost.objects.all()

    if search_query:
        jobs = jobs.filter(title__icontains=search_query)
    if category_id:
        jobs = jobs.filter(category__id=category_id)
    if country_id:
        jobs = jobs.filter(country__id=country_id)

    return render(request, "jobs/partials/job_results.html", {"jobs": jobs})


def unlock_hr_info(request, job_id):
    """Allows users to spend 10 credits to unlock HR contact info before applying."""
    job = get_object_or_404(JobPost, id=job_id)
    seeker = request.user

    # Check if an application exists, if not, create one just for unlocking
    application, created = Application.objects.get_or_create(seeker=seeker, job=job)

    if not application.hr_unlocked:
        if seeker.credits >= 10:
            seeker.credits -= 10  # Deduct credits
            seeker.save(update_fields=["credits"])
            application.hr_unlocked = True
            application.save(update_fields=["hr_unlocked"])
            messages.success(request, "HR contact information unlocked!")
        else:
            messages.error(request, "Not enough credits to unlock HR contact info.")

    return redirect("jobs:job_detail", job.id)


def buy_priority_review(request, application_id):
    application = get_object_or_404(Application, id=application_id)
    seeker = application.seeker

    if seeker != request.user:
        messages.error(request, "Unauthorized action.")
        return redirect("dashboard")  # Redirect to dashboard instead

    if application.priority_review:
        messages.info(request, "You have already purchased priority HR review.")
    elif seeker.credits >= 15:
        seeker.credits -= 15
        seeker.save(update_fields=["credits"])
        application.priority_review = True
        application.save(update_fields=["priority_review"])
        messages.success(request, "Priority HR review purchased successfully!")
    else:
        messages.error(request, "Insufficient credits to buy priority HR review.")

    return redirect("seeker:dashboard")  # Updated redirect


@login_required
def unlock_exclusive_jobs(request):
    """Handles unlocking all exclusive jobs for 3 days using credits, with 3-day cooldown."""
    seeker = request.user

    # ✅ Check cooldown
    can_unlock, seconds_remaining, cooldown_end = seeker.can_unlock_exclusive_jobs()
    if not can_unlock:
        days_remaining = int(seconds_remaining // 86400)
        messages.warning(request, f"⏳ You can unlock exclusive jobs again in {days_remaining} day(s).")
        return redirect("seeker:dashboard")

    # ✅ Check credits
    if seeker.credits >= 10:
        seeker.credits -= 10
        seeker.save(update_fields=["credits"])

        # Unlock each exclusive job
        for job in JobPost.objects.filter(exclusive_job=True):
            UnlockedExclusiveJob.objects.create(
                seeker=seeker,
                job=job,
                expires_at=now() + timedelta(days=3)
            )

        # ✅ In-app notification
        Notification.objects.create(
            seeker=seeker,
            message="🔓 You’ve unlocked all exclusive jobs for 3 days! Check them out in your dashboard."
        )

        # ✅ Schedule expiration notification
        schedule(
            func=notify_expiration,
            seeker=seeker,
            next_run=now() + timedelta(days=3)
        )

        # Create or update HiddenJobAccess for admin visibility
        hidden_access, created = HiddenJobAccess.objects.get_or_create(
            seeker=seeker,
            active=True,
            defaults={"expires_at": now() + timedelta(days=3)}
        )

        # If existing and expired, extend it
        if not created and hidden_access.expires_at < now():
            hidden_access.expires_at = now() + timedelta(days=3)
            hidden_access.active = True
            hidden_access.save(update_fields=["expires_at", "active"])

        messages.success(request, "🎉 You have unlocked exclusive jobs for 3 days! Check the new 'Exclusive Jobs' section.")
    else:
        messages.error(request, "❌ Not enough credits to unlock exclusive job listings.")

    return redirect("seeker:dashboard")


@login_required
def recommended_jobs(request):
    """Displays jobs recommended to the seeker based on their job title category."""
    seeker = request.user
    recommended = []

    if seeker.job_title and seeker.job_title.category:
        recommended = list(
            JobPost.objects.filter(
                category=seeker.job_title.category,
                exclusive_job=False
            ).distinct().order_by("-created_at")  # You can sort by any field you like
        )

    return render(request, "jobs/recommended_jobs.html", {
        "recommended_jobs": recommended
    })


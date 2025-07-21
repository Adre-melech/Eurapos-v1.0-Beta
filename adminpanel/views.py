from datetime import timedelta
from django.db.models import Avg, Max, Count
from django.db.models import Count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.timezone import now
from django.views.decorators.http import require_POST

from jobs.models import UnlockedExclusiveJob
from events.models import TicketPurchase, EventTicket
from jobs.models import JobPost, Application, Category, JobTitle, JobCountry, SeekerCountry
from seeker.models import Seeker, ATSResumeRequest, VisaDiscount, UnlockedVisaGuide, VisaGuide, UserActivity, \
    SuspiciousLoginAlert
from notifications.models import Notification
from collections import defaultdict
from adminpanel.models import AdminNotification, HiddenJobAccess

def is_staff_user(user):
    """Checks if the user is a staff member"""
    return user.is_authenticated and user.is_staff

@user_passes_test(is_staff_user)
@login_required
def admin_dashboard(request):
    """Displays the admin panel with job and seeker management"""
    jobs_count = JobPost.objects.count()
    applications_count = Application.objects.count()
    seekers_count = Seeker.objects.filter(is_staff=False).count()
    notifications_count = Notification.objects.filter(read=False).count()
    seekers = Seeker.objects.filter(is_staff=False)
    jobs = JobPost.objects.all()
    categories = Category.objects.all()
    job_titles = JobTitle.objects.all()
    job_countries = JobCountry.objects.all()
    seeker_countries = SeekerCountry.objects.all()

    recent_applications = Application.objects.select_related('seeker', 'job').order_by('-applied_at')[:10]
    priority_applications = Application.objects.filter(
        priority_review=True
    ).select_related('seeker', 'job').order_by('-purchased_priority_at')[:10]

    whatsapp_users = Seeker.objects.filter(
        receive_whatsapp_jobs=True,
        whatsapp_optin_expires__gte=now()
    ).order_by("-whatsapp_optin_expires")[:10]
    pending_tickets = TicketPurchase.objects.filter(confirmed=False).select_related('seeker', 'event').order_by(
        '-purchased_at')[:10]
    ats_requests = ATSResumeRequest.objects.filter(processed=False).order_by("-requested_at")


    return render(request, "adminpanel/dashboard.html", {
        "jobs_count": jobs_count,
        "applications_count": applications_count,
        "seekers_count": seekers_count,
        "notifications_count": notifications_count,
        "seekers": seekers,
        "applications": recent_applications,
        "jobs": jobs,
        "categories": categories,
        "job_titles": job_titles,
        "job_countries": job_countries,
        "seeker_countries": seeker_countries,
        "whatsapp_users": whatsapp_users,
        "pending_tickets": pending_tickets,
        "ats_requests": ats_requests,
        "priority_applications": priority_applications,
        "now": now,
    })


@staff_member_required
def all_applications(request):
    apps = Application.objects.select_related('seeker', 'job').order_by('-applied_at')
    return render(request, "adminpanel/all_applications.html", {"applications": apps})


@staff_member_required
def ats_requests_list(request):
    """View to list all ATS CV requests for admin"""
    ats_requests = ATSResumeRequest.objects.select_related('seeker').order_by('-requested_at')

    context = {
        "ats_requests": ats_requests
    }
    return render(request, "adminpanel/ats_requests_list.html", context)


@staff_member_required
def upload_ats_cv(request, request_id):
    """Handles admin upload of ATS CV for a seeker"""
    from seeker.models import ATSResumeRequest  # if not already imported
    ats_request = get_object_or_404(ATSResumeRequest, id=request_id)

    if request.method == "POST" and request.FILES.get("cv_file"):
        ats_request.cv_file = request.FILES["cv_file"]
        ats_request.processed = True
        ats_request.save(update_fields=["cv_file", "processed"])

        from notifications.models import Notification
        Notification.objects.create(
            seeker=ats_request.seeker,
            message=f"📄 Your ATS-optimized CV for order {ats_request.order_id} has been uploaded! Download it from your dashboard."
        )

        messages.success(request, f"ATS CV uploaded for {ats_request.seeker.username}.")
    else:
        messages.error(request, "Please upload a valid file.")

    return redirect("adminpanel:admin_dashboard")


@staff_member_required
def mark_ats_processed(request, request_id):
    """Marks an ATS CV request as processed"""
    ats_request = get_object_or_404(ATSResumeRequest, id=request_id)
    if request.method == "POST":
        ats_request.processed = True
        ats_request.save(update_fields=["processed"])
        messages.success(request, f"ATS CV order {ats_request.order_id} marked as processed.")
    return redirect("adminpanel:admin_dashboard")


@staff_member_required
def delivered_ats_resumes_list(request):
    """Lists all successfully processed ATS resume deliveries."""
    delivered_ats_resumes = (
        ATSResumeRequest.objects
        .filter(processed=True, cv_file__isnull=False)
        .select_related("seeker")
        .order_by("-requested_at")
    )

    return render(request, "adminpanel/delivered_ats_resumes.html", {
        "delivered_resumes": delivered_ats_resumes
    })


def admin_login(request):
    """Handles admin staff login"""
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user and user.is_staff:
            login(request, user)
            messages.success(request, "Welcome to the Admin Panel!")
            return redirect("adminpanel:admin_dashboard")
        else:
            messages.error(request, "Invalid credentials or insufficient permissions.")

    return render(request, "adminpanel/login.html")

@login_required
def admin_logout(request):
    """Logs out the admin user"""
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect("adminpanel:admin_login")

@staff_member_required
def add_job(request):
    """Allows admin to post a job"""
    if request.method == "POST":
        title = request.POST.get("title")
        company_name = request.POST.get("company_name")
        salary = request.POST.get("salary")
        deadline = request.POST.get("deadline")
        category_id = request.POST.get("category")
        country_id = request.POST.get("country")

        category = get_object_or_404(Category, id=category_id)
        country = get_object_or_404(JobCountry, id=country_id)

        JobPost.objects.create(
            title=title,
            company_name=company_name,
            salary=salary,
            deadline=deadline,
            category=category,
            country=country
        )

        # ✅ Notify all seekers of new job post
        for seeker in Seeker.objects.filter(is_staff=False):
            Notification.objects.create(
                seeker=seeker,
                message=f"💼 A new job '{title}' has been posted at {company_name}. Check it out!"
            )

        messages.success(request, "Job posted successfully!")
        return redirect("adminpanel:admin_dashboard")

    categories = Category.objects.all()
    countries = JobCountry.objects.all()

    return render(request, "adminpanel/add_job.html", {"categories": categories, "countries": countries})


@staff_member_required
def manage_jobs(request):
    """Displays all posted jobs for admins to edit or delete."""
    jobs = JobPost.objects.all()
    return render(request, "adminpanel/manage_jobs.html", {"jobs": jobs})

@staff_member_required
def delete_job(request, job_id):
    """Deletes a job post."""
    job = get_object_or_404(JobPost, id=job_id)

    if request.method == "POST":  # Ensure deletion only happens via POST request
        job.delete()
        messages.success(request, f"Job '{job.title}' has been deleted.")
        return redirect("adminpanel:manage_jobs")

    return render(request, "adminpanel/confirm_delete_job.html", {"job": job})

@staff_member_required
def edit_job(request, job_id):
    """Allows admins to edit a job post."""
    job = get_object_or_404(JobPost, id=job_id)

    if request.method == "POST":
        job.title = request.POST.get("title")
        job.company_name = request.POST.get("company_name")
        job.salary = request.POST.get("salary")
        job.deadline = request.POST.get("deadline")
        job.description = request.POST.get("description")
        job.required_skills = request.POST.get("required_skills")
        job.save()
        messages.success(request, "Job updated successfully.")
        return redirect("adminpanel:manage_jobs")

    return render(request, "adminpanel/edit_job.html", {"job": job})



@staff_member_required
def add_category(request):
    """Allows admin to add job categories"""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            Category.objects.create(name=name)

            # ✅ Notify all seekers about new job category
            for seeker in Seeker.objects.filter(is_staff=False):
                Notification.objects.create(
                    seeker=seeker,
                    message=f"🆕 We've added a new job category: {name}. Explore new opportunities!"
                )

            messages.success(request, "Category added successfully!")
            return redirect("adminpanel:admin_dashboard")
    return render(request, "adminpanel/add_category.html")


@staff_member_required
def manage_categories(request):
    """Displays all job categories for admins to edit or delete"""
    return render(request, "adminpanel/manage_categories.html", {"categories": Category.objects.all()})

@staff_member_required
def edit_category(request, category_id):
    """Allows admin to edit a job category"""
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.name = request.POST.get("name", category.name)
        category.save()
        messages.success(request, "Category updated successfully.")
        return redirect("adminpanel:manage_categories")

    return render(request, "adminpanel/edit_category.html", {"category": category})

@staff_member_required
def delete_category(request, category_id):
    """Deletes a job category"""
    category = get_object_or_404(Category, id=category_id)

    if request.method == "POST":
        category.delete()
        messages.success(request, f"Category '{category.name}' has been deleted.")
        return redirect("adminpanel:manage_categories")

    return render(request, "adminpanel/confirm_delete_category.html", {"category": category})


@staff_member_required
def add_job_title(request):
    """Allows admin to add job titles"""
    if request.method == "POST":
        name = request.POST.get("name")
        category_id = request.POST.get("category")
        category = get_object_or_404(Category, id=category_id)

        if name and category:
            JobTitle.objects.create(name=name, category=category)

            # ✅ Notify all seekers about new job title
            for seeker in Seeker.objects.filter(is_staff=False):
                Notification.objects.create(
                    seeker=seeker,
                    message=f"🆕 We've added a new job title: {name}. More career paths await!"
                )

            messages.success(request, "Job Title added successfully!")
            return redirect("adminpanel:admin_dashboard")

    categories = Category.objects.all()
    return render(request, "adminpanel/add_job_title.html", {"categories": categories})


@staff_member_required
def manage_job_titles(request):
    """Displays all job titles for admins to edit or delete"""
    return render(request, "adminpanel/manage_job_titles.html", {"job_titles": JobTitle.objects.all()})

@staff_member_required
def edit_job_title(request, job_title_id):
    """Allows admin to edit a job title"""
    job_title = get_object_or_404(JobTitle, id=job_title_id)

    if request.method == "POST":
        job_title.name = request.POST.get("name", job_title.name)
        job_title.save()
        messages.success(request, "Job Title updated successfully.")
        return redirect("adminpanel:manage_job_titles")

    return render(request, "adminpanel/edit_job_title.html", {"job_title": job_title})

@staff_member_required
def delete_job_title(request, job_title_id):
    """Deletes a job title"""
    job_title = get_object_or_404(JobTitle, id=job_title_id)

    if request.method == "POST":
        job_title.delete()
        messages.success(request, f"Job Title '{job_title.name}' has been deleted.")
        return redirect("adminpanel:manage_job_titles")

    return render(request, "adminpanel/confirm_delete_job_title.html", {"job_title": job_title})


@staff_member_required
def add_seeker_country(request):
    """Allows admin to add seeker countries"""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            SeekerCountry.objects.create(name=name)
            messages.success(request, "Seeker Country added successfully!")
            return redirect("adminpanel:admin_dashboard")

    return render(request, "adminpanel/add_seeker_country.html")


@staff_member_required
def update_application_status(request, application_id):
    """Manually update the status of a job application from the dashboard."""
    application = get_object_or_404(Application, id=application_id)

    if request.method == "POST":
        new_status = request.POST.get("status")
        valid_statuses = dict(Application.STATUS_CHOICES).keys()

        if new_status in valid_statuses:
            application.status = new_status
            application.save(update_fields=["status"])
            messages.success(request, f"Status updated to '{new_status}' for {application.seeker.username}.")
        else:
            messages.error(request, "Invalid status selected.")

    return redirect("adminpanel:admin_dashboard")


@staff_member_required
def manage_seeker_countries(request):
    """Displays all seeker countries for admins to edit or delete"""
    return render(request, "adminpanel/manage_seeker_countries.html", {"seeker_countries": SeekerCountry.objects.all()})

@staff_member_required
def edit_seeker_country(request, country_id):
    """Allows admin to edit a seeker country"""
    country = get_object_or_404(SeekerCountry, id=country_id)

    if request.method == "POST":
        country.name = request.POST.get("name", country.name)
        country.save()
        messages.success(request, "Seeker Country updated successfully.")
        return redirect("adminpanel:manage_seeker_countries")

    return render(request, "adminpanel/edit_seeker_country.html", {"country": country})


@staff_member_required
def delete_seeker_country(request, country_id):
    """Deletes a seeker country"""
    country = get_object_or_404(SeekerCountry, id=country_id)

    if request.method == "POST":
        country.delete()
        messages.success(request, f"Seeker Country '{country.name}' has been deleted.")
        return redirect("adminpanel:manage_seeker_countries")

    return render(request, "adminpanel/confirm_delete_seeker_country.html", {"country": country})


@staff_member_required
def add_job_country(request):
    """Allows admin to add job countries"""
    if request.method == "POST":
        name = request.POST.get("name")
        if name:
            JobCountry.objects.create(name=name)

            # ✅ Notify all seekers about new job country
            for seeker in Seeker.objects.filter(is_staff=False):
                Notification.objects.create(
                    seeker=seeker,
                    message=f"🌍 We've added a new country: {name}. Explore opportunities abroad!"
                )

            messages.success(request, "Job Country added successfully!")
            return redirect("adminpanel:admin_dashboard")

    return render(request, "adminpanel/add_job_country.html")


@staff_member_required
def manage_exclusive_access(request):
    seekers = Seeker.objects.all().order_by("username")

    if request.method == "POST":
        seeker_id = request.POST.get("seeker_id")
        action = request.POST.get("action")
        seeker = get_object_or_404(Seeker, id=seeker_id)

        if action == "grant":
            expires = now() + timedelta(days=3)
            exclusive_jobs = JobPost.objects.filter(exclusive_job=True)

            for job in exclusive_jobs:
                UnlockedExclusiveJob.objects.update_or_create(
                    seeker=seeker,
                    job=job,
                    defaults={"expires_at": expires, "active": True}
                )

            # (Re)create or update HiddenJobAccess (for cooldown tracking)
            HiddenJobAccess.objects.update_or_create(
                seeker=seeker,
                defaults={"expires_at": expires, "active": True}
            )

            Notification.objects.create(
                seeker=seeker,
                message="🎉 Eurapos has granted you access to exclusive job listings for 3 days!"
            )

            messages.success(request, f"✅ Exclusive job access granted to {seeker.username} for 3 days.")

        elif action == "revoke":
            # Revoke all current exclusive jobs
            UnlockedExclusiveJob.objects.filter(seeker=seeker).update(active=False)

            # ❌ Clear cooldown logic so user can buy again
            HiddenJobAccess.objects.filter(seeker=seeker).delete()
            UnlockedExclusiveJob.objects.filter(seeker=seeker).delete()

            Notification.objects.create(
                seeker=seeker,
                message="🚫 Your access to exclusive job listings has been revoked by Eurapos."
            )

            messages.warning(request, f"🚫 Exclusive job access revoked for {seeker.username}.")

        return redirect("adminpanel:manage_exclusive_access")

    seekers_with_access = {
        seeker.id: UnlockedExclusiveJob.objects.filter(
            seeker=seeker, expires_at__gt=now(), active=True
        ).exists()
        for seeker in seekers
    }

    return render(request, "adminpanel/manage_exclusive_access.html", {
        "seekers": seekers,
        "seekers_with_access": seekers_with_access,
    })


@staff_member_required
def manage_job_countries(request):
    """Displays all job countries for admins to edit or delete"""
    return render(request, "adminpanel/manage_job_countries.html", {"job_countries": JobCountry.objects.all()})

@staff_member_required
def edit_job_country(request, country_id):
    """Allows admin to edit a job country"""
    country = get_object_or_404(JobCountry, id=country_id)

    if request.method == "POST":
        country.name = request.POST.get("name", country.name)
        country.save()
        messages.success(request, "Job Country updated successfully.")
        return redirect("adminpanel:manage_job_countries")

    return render(request, "adminpanel/edit_job_country.html", {"country": country})

@staff_member_required
def delete_job_country(request, country_id):
    """Deletes a job country"""
    country = get_object_or_404(JobCountry, id=country_id)

    if request.method == "POST":
        country.delete()
        messages.success(request, f"Job Country '{country.name}' has been deleted.")
        return redirect("adminpanel:manage_job_countries")

    return render(request, "adminpanel/confirm_delete_job_country.html", {"country": country})


@staff_member_required
def manage_seeker(request, seeker_id):
    """View, edit & delete a seeker profile"""
    seeker = get_object_or_404(Seeker, id=seeker_id)

    if request.method == "POST" and "delete" in request.POST:
        seeker.delete()
        messages.success(request, "Seeker profile deleted successfully.")
        return redirect("adminpanel:admin_dashboard")

    if request.method == "POST" and "update" in request.POST:
        seeker.full_name = request.POST.get("full_name", seeker.full_name)
        seeker.email = request.POST.get("email", seeker.email)
        seeker.phone = request.POST.get("phone", seeker.phone)
        seeker.address = request.POST.get("address", seeker.address)
        seeker.country = get_object_or_404(SeekerCountry, id=request.POST.get("country", seeker.country.id))
        seeker.job_title = get_object_or_404(JobTitle, id=request.POST.get("job_title", seeker.job_title.id))
        seeker.save()
        messages.success(request, "Seeker profile updated successfully.")
        return redirect("adminpanel:manage_seeker", seeker_id=seeker.id)

    countries = SeekerCountry.objects.all()
    job_titles = JobTitle.objects.all()

    return render(request, "adminpanel/manage_seeker.html", {
        "seeker": seeker,
        "countries": countries,
        "job_titles": job_titles
    })


@staff_member_required
def manage_all_seekers(request):
    seekers = Seeker.objects.filter(is_staff=False).order_by("-date_joined")

    if request.method == "POST":
        seeker_id = request.POST.get("seeker_id")
        credits = int(request.POST.get("credits", 0))

        if seeker_id and credits > 0:
            seeker = get_object_or_404(Seeker, id=seeker_id)
            seeker.credits += credits
            seeker.save(update_fields=["credits"])

            from notifications.models import Notification
            Notification.objects.create(
                seeker=seeker,
                message=f"💰 {credits} credits were added to your account by Eurapos!"
            )

            messages.success(request, f"{credits} credits added to {seeker.username}.")

        return redirect("adminpanel:manage_all_seekers")

    return render(request, "adminpanel/manage_all_seekers.html", {"seekers": seekers})


@staff_member_required
def delete_seeker(request, seeker_id):
    """Deletes a seeker account along with related applications"""
    seeker = get_object_or_404(Seeker, id=seeker_id)

    if request.method == "POST":  # Ensure deletion only happens via POST request
        seeker.delete()
        messages.success(request, f"Seeker '{seeker.username}' has been deleted.")
        return redirect("adminpanel:admin_dashboard")

    return render(request, "adminpanel/confirm_delete_seeker.html", {"seeker": seeker})


@staff_member_required
def manage_credits(request, seeker_id):
    """Manages user credits (add/redeem)"""
    seeker = get_object_or_404(Seeker, id=seeker_id)

    if request.method == "POST":
        credit_amount = int(request.POST.get("credits", 0))
        if credit_amount > 0:
            seeker.credits += credit_amount
            seeker.save(update_fields=["credits"])

            # ✅ Notify seeker about credit addition
            from notifications.models import Notification
            Notification.objects.create(
                seeker=seeker,
                message=f"💰 {credit_amount} credits were added to your account by Eurapos!"
            )

            messages.success(request, f"{credit_amount} credits added to {seeker.username}.")
        else:
            messages.warning(request, "No credits were added. Please enter a positive amount.")

        return redirect("adminpanel:admin_dashboard")

    return render(request, "adminpanel/manage_credits.html", {"seeker": seeker})


@staff_member_required
def add_event(request):
    """Handles event creation by the admin."""
    if request.method == "POST":
        title = request.POST.get("title")
        image = request.FILES.get("image")
        credits_required = request.POST.get("credits_required")
        available_until = request.POST.get("available_until")
        description = request.POST.get("description")

        if title and image and credits_required and available_until:
            EventTicket.objects.create(
                title=title,
                image=image,
                credits_required=credits_required,
                available_until=available_until,
                description=description,
            )
            messages.success(request, "✅ Event added successfully!")
            return redirect("adminpanel:manage_events")
        else:
            messages.error(request, "❌ All fields are required!")

    return render(request, "adminpanel/add_event.html")


@staff_member_required
def manage_events(request):
    """Displays all events for admin management."""
    events = EventTicket.objects.all().order_by("-available_until")
    return render(request, "adminpanel/manage_events.html", {"events": events})


@staff_member_required
def edit_event(request, event_id):
    """Allows admins to edit existing events."""
    event = get_object_or_404(EventTicket, id=event_id)

    if request.method == "POST":
        event.title = request.POST.get("title", event.title)
        event.credits_required = request.POST.get("credits_required", event.credits_required)
        event.available_until = request.POST.get("available_until", event.available_until)
        event.description = request.POST.get("description", event.description)

        if request.FILES.get("image"):
            event.image = request.FILES.get("image")

        event.save()
        messages.success(request, "✅ Event updated successfully!")
        return redirect("adminpanel:manage_events")

    return render(request, "adminpanel/edit_event.html", {"event": event})


@staff_member_required
def delete_event(request, event_id):
    """Allows admins to delete events."""
    event = get_object_or_404(EventTicket, id=event_id)

    if request.method == "POST":
        event.delete()
        messages.success(request, "🗑 Event deleted successfully!")
        return redirect("adminpanel:manage_events")

    return render(request, "adminpanel/confirm_delete_event.html", {"event": event})


@staff_member_required
def add_visa_guide(request):
    """Allows admin to upload a Visa Guide."""
    if request.method == "POST":
        country = request.POST.get("country")
        image = request.FILES.get("image")
        pdf_file = request.FILES.get("pdf_file")
        credits_required = request.POST.get("credits_required")

        if country and image and pdf_file and credits_required:
            VisaGuide.objects.create(
                country=country,
                image=image,
                pdf_file=pdf_file,
                credits_required=credits_required,
            )
            messages.success(request, "✅ Visa Guide added successfully!")
            return redirect("adminpanel:manage_visa_guides")
        else:
            messages.error(request, "❌ All fields are required!")

    return render(request, "adminpanel/add_visa.html")


@staff_member_required
def manage_visa_guides(request):
    """Displays all uploaded Visa Guides for admin management."""
    visa_guides = VisaGuide.objects.all().order_by("country")
    return render(request, "adminpanel/manage_visa_guides.html", {"visa_guides": visa_guides})


@staff_member_required
def edit_visa_guide(request, visa_guide_id):
    """Allows admins to edit existing Visa Guides."""
    visa_guide = get_object_or_404(VisaGuide, id=visa_guide_id)

    if request.method == "POST":
        visa_guide.country = request.POST.get("country", visa_guide.country)
        visa_guide.credits_required = request.POST.get("credits_required", visa_guide.credits_required)

        if request.FILES.get("image"):
            visa_guide.image = request.FILES.get("image")
        if request.FILES.get("pdf_file"):
            visa_guide.pdf_file = request.FILES.get("pdf_file")

        visa_guide.save()
        messages.success(request, "✅ Visa Guide updated successfully!")
        return redirect("adminpanel:manage_visa_guides")

    return render(request, "adminpanel/edit_visa.html", {"visa_guide": visa_guide})


@staff_member_required
def delete_visa_guide(request, visa_guide_id):
    """Allows admins to delete Visa Guides."""
    visa_guide = get_object_or_404(VisaGuide, id=visa_guide_id)

    if request.method == "POST":
        visa_guide.delete()
        messages.success(request, "🗑 Visa Guide deleted successfully!")
        return redirect("adminpanel:manage_visa_guides")

    return render(request, "adminpanel/confirm_delete_visa.html", {"visa_guide": visa_guide})


@staff_member_required
def upload_event_ticket(request, ticket_id):
    ticket = get_object_or_404(TicketPurchase, pk=ticket_id)
    if request.method == 'POST' and request.FILES.get('ticket_file'):
        ticket.ticket_file = request.FILES['ticket_file']
        ticket.generate_confirmation_code()
        ticket.save()
        messages.success(request, f"✅ Ticket uploaded for {ticket.seeker.username}.")
    return redirect('adminpanel:dashboard')


@staff_member_required
def confirm_event_ticket(request, ticket_id):
    ticket = get_object_or_404(TicketPurchase, pk=ticket_id)
    if request.method == 'POST':
        ticket.confirmed = True
        ticket.save(update_fields=['confirmed'])
        messages.success(request, f"✅ Ticket confirmed for {ticket.seeker.username}.")
    return redirect('adminpanel:dashboard')


@staff_member_required
def mark_ticket_delivered(request, ticket_id):
    ticket = get_object_or_404(TicketPurchase, id=ticket_id)
    ticket.confirmed = True  # Marks as delivered
    ticket.save(update_fields=["confirmed"])

    from notifications.models import Notification
    Notification.objects.create(
        seeker=ticket.seeker,
        message=f"🎟️ Your ticket for '{ticket.event.title}' has been marked as delivered!"
    )

    messages.success(request, "✅ Ticket marked as delivered.")
    return redirect("adminpanel:admin_dashboard")

@staff_member_required
def priority_applications_list(request):
    priority_applications = Application.objects.filter(
        priority_review=True
    ).select_related('seeker', 'job').order_by('-purchased_priority_at')
    return render(request, "adminpanel/priority_application_list.html", {"priority_applications": priority_applications})

@staff_member_required
def whatsapp_subscribers_list(request):
    whatsapp_users = Seeker.objects.filter(
        receive_whatsapp_jobs=True,
        whatsapp_optin_expires__gte=now()
    ).order_by("-whatsapp_optin_expires")
    return render(request, "adminpanel/whatsapp_subscribers_list.html", {"whatsapp_users": whatsapp_users})

@staff_member_required
def mark_priority_done(request, app_id):
    application = get_object_or_404(Application, pk=app_id, priority_review=True)
    if request.method == 'POST':
        application.priority_review = False  # Mark it as processed
        application.save(update_fields=['priority_review'])
        messages.success(request, f"✅ Priority review marked as done for {application.seeker.username}.")
    return redirect('adminpanel:admin_dashboard')


@staff_member_required
def all_pending_event_tickets(request):
    """Lists all pending event ticket requests for admin review."""
    pending_tickets = (
        TicketPurchase.objects
        .filter(confirmed=False)
        .select_related("seeker", "event")  # Adjust related fields if applicable
        .order_by("-purchased_at")
    )

    return render(request, "adminpanel/all_pending_event_tickets.html", {
        "pending_tickets": pending_tickets
    })


@staff_member_required
def delivered_event_tickets(request):
    """Lists all confirmed (delivered) event ticket purchases."""
    delivered_tickets = (
        TicketPurchase.objects
        .filter(confirmed=True)
        .select_related('seeker', 'event')
        .order_by('-purchased_at')
    )

    return render(request, "adminpanel/delivered_event_tickets.html", {
        "delivered_tickets": delivered_tickets
    })


@staff_member_required
def unlocked_access_users(request):
    """Lists seekers who have unlocked exclusive jobs, visa guides, or purchased visa discounts."""
    unlocked_jobs_access = (
        UnlockedExclusiveJob.objects
        .filter(expires_at__gte=now())
        .select_related("seeker")
        .order_by("-unlocked_at")
    )

    unlocked_visa_guides = (
        UnlockedVisaGuide.objects
        .select_related("seeker", "guide")
        .order_by("-unlocked_at")
    )

    visa_purchases = (
        VisaDiscount.objects
        .select_related("seeker")
        .order_by("-purchased_at")
    )

    return render(request, "adminpanel/unlocked_access_users.html", {
        "unlocked_jobs": unlocked_jobs_access,
        "unlocked_visa_guides": unlocked_visa_guides,
        "visa_purchases": visa_purchases,
    })


def activity_summary(request):
    data = UserActivity.objects.values("is_authenticated").annotate(count=Count("id"))
    return render(request, "adminpanel/activity_summary.html", {"data": data})


def alert_dashboard(request):
    stats = SuspiciousLoginAlert.objects.aggregate(
        avg_score=Avg("behavior_score"),
        max_score=Max("behavior_score"),
        total_alerts=Count("id")
    )
    return render(request, "admin/alert_dashboard.html", {"stats": stats})


def admin_notifications_view(request):
    all_notifications = AdminNotification.objects.all().order_by("-created_at")
    categories = [
        {"key": "job_application", "label": "Job Application"},
        {"key": "priority_application", "label": "Priority Application"},
        {"key": "whatsapp_job", "label": "WhatsApp Job"},
        {"key": "ats_cv_request", "label": "ATS CV Request"},
        {"key": "event_ticket", "label": "Event Ticket"},
        {"key": "visa_guide", "label": "Visa Guide"},
        {"key": "contact_form", "label": "Contact Form"},
    ]

    grouped = defaultdict(list)
    for note in all_notifications:
        grouped[note.type].append(note)

    return render(request, "adminpanel/notifications.html", {
        "grouped": dict(grouped),
        "categories": categories
    })

@require_POST
def mark_as_read(request, notification_id):
    note = get_object_or_404(AdminNotification, id=notification_id)
    note.mark_as_read()
    return redirect("adminpanel:admin_notifications_view")


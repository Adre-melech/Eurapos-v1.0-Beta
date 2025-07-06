from django.shortcuts import render, redirect
from django.contrib import messages
from django.core.mail import mail_admins
from recruiter.models import PartnerRegistration


def why_partner(request):
    return render(request, "recruiter/why_partner.html")

def resume_access(request):
    return render(request, "recruiter/resume_access.html")

def workforce_solutions(request):
    return render(request, "recruiter/workforce_solutions.html")

def post_jobs(request):
    return render(request, "recruiter/post_jobs.html")


def partner_register(request):
    if request.method == "POST":
        company = request.POST.get("company")
        email = request.POST.get("email")

        if company and email:
            # Avoid duplication errors gracefully
            obj, created = PartnerRegistration.objects.get_or_create(company=company, email=email)

            if created:
                # ✅ Notify admins instantly
                mail_admins(
                    subject="📩 New Partner Registration",
                    message=f"Company: {company}\nEmail: {email}"
                )
                messages.success(request, "🎉 Thank you! Our team will reach out shortly.")
            else:
                messages.warning(request, "✅ You're already registered! We'll be in touch soon.")
        else:
            messages.error(request, "❌ Please fill out all fields.")

    return redirect(request.META.get("HTTP_REFERER", "/"))



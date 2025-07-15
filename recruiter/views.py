from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib import messages
from django.core.mail import mail_admins
from django.core.mail import send_mail
from django.conf import settings
from .models import PartnerRegistration, ResumeAccessOrder
from django.views.decorators.csrf import csrf_exempt
import json


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


@csrf_exempt
def place_resume_access_order(request):
    if request.method == "POST":
        data = json.loads(request.body)
        ResumeAccessOrder.objects.create(
            plan=data.get("plan"),
            company_name=data.get("company_name", ""),
            name=data.get("name"),
            phone=data.get("phone"),
            email=data.get("email")
        )

        # ✅ Confirmation email to recruiter
        send_mail(
            "✅ Eurapos Resume Access Request Received",
            "Thank you for submitting your request. Our team will be in touch soon with your access credentials.",
            settings.DEFAULT_FROM_EMAIL,
            [ResumeAccessOrder.email],
            fail_silently=False
        )

        return JsonResponse({"status": "success"})
    return JsonResponse({"status": "error"}, status=400)


def notify_admin(order):
    subject = f"📩 New Resume Access Order – {order.plan.title()}"
    message = (
        f"Company: {order.company_name or 'N/A'}\n"
        f"Name: {order.name}\n"
        f"Phone: {order.phone}\n"
        f"Email: {order.email}\n"
        f"Plan: {order.get_plan_display()}\n"
        f"Ordered at: {order.created_at.strftime('%Y-%m-%d %H:%M')}"
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [settings.ADMIN_NOTIFICATION_EMAIL],  # You can set this in settings.py
        fail_silently=False
    )

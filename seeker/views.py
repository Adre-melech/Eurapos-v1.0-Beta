import os
from django.conf import settings
import random, string
import logging
from django.contrib.auth.decorators import login_required
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import PasswordResetView
from django.core.mail import send_mail, BadHeaderError
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.http import urlsafe_base64_encode
from django.utils.timezone import now, timedelta
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm
from django.contrib import messages
from datetime import date
from django.utils.encoding import force_bytes
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from events.models import TicketPurchase
from .forms import SeekerRegistrationForm, SeekerPasswordResetForm
from jobs.models import Application, UnlockedExclusiveJob
from notifications.models import Notification
from .utils import generate_visa_discount_pdf
from .models import Seeker, ATSResumeRequest, VisaDiscount, VisaGuide, UnlockedVisaGuide


logger = logging.getLogger(__name__)


def seeker_register(request):
    """Handles seeker registration, grants bonus credits, tracks referrals, and sends a welcome notification."""
    if request.method == "POST":
        form = SeekerRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.add_credits(5)  # Grant 5 bonus credits on registration

            # Check if the user was referred by another seeker
            referral_code = request.POST.get("referral_id")  # Get referral ID from input
            referrer = Seeker.objects.filter(referral_id=referral_code).first()

            if referrer:
                user.referred_by = referrer  # Link referral
                user.save(update_fields=["referred_by"])
                referrer.award_referral_bonus(referrer)  # Award 50 credits to the referrer

            login(request, user)
            Notification.objects.create(
                seeker=user,
                message="Welcome to Eurapos! Your account has been created successfully. You've received 5 bonus credits!"
            )
            messages.success(request, "Registration successful! You've earned 5 credits.")
            return redirect('jobs:job_list')
        else:
            messages.error(request, "Registration failed. Please check your inputs.")
    else:
        form = SeekerRegistrationForm()

    return render(request, 'seeker/register.html', {'form': form})


def seeker_login(request):
    """Handles seeker login and grants 5 credits for daily logins."""
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_superuser:
                messages.error(request, "Admin users cannot log in via the seeker portal. Please use the admin panel.")
                return redirect("seeker:seeker_login")

            # Grant 5 credits for daily login
            user.grant_daily_login_reward()
            login(request, user)

            messages.success(request, f"Welcome back, {user.username}! 🎉 You earned **5 credits** for logging in today!")

            return redirect("seeker:dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.")
    else:
        form = AuthenticationForm()

    return render(request, "seeker/login.html", {"form": form})


@csrf_exempt
def custom_password_reset_view(request):
    if request.method == "POST":
        form = SeekerPasswordResetForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"]
            users = form.get_users(email)

            for user in users:
                context = {
                    "email": user.email,
                    "domain": request.get_host(),
                    "site_name": "Eurapos",
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    "token": default_token_generator.make_token(user),
                    "protocol": "https" if request.is_secure() else "http",
                }

                subject = render_to_string("seeker/registration/password_reset_subject.txt", context).strip()
                email_body = render_to_string("seeker/registration/password_reset_email.html", context)

                send_mail(
                    subject,
                    email_body,
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

            return render(request, "seeker/password_reset_ajax.html")

        else:
            return HttpResponse("This email address doesn't exist", status=200)

    else:
        form = SeekerPasswordResetForm()
    return render(request, "seeker/password_reset_form.html", {"form": form})

def seeker_logout(request):
    """Handles seeker logout"""
    logout(request)
    messages.success(request, "You have logged out successfully.")
    return redirect('home:home')  # Redirect to homepage


def seeker_dashboard(request):
    """Displays seeker job applications and account info."""
    if not request.user.is_authenticated:
        messages.error(request, "You need to log in to view your dashboard.")
        return redirect("seeker:seeker_login")

    seeker = request.user

    applications = Application.objects.filter(seeker=seeker).order_by("-applied_at")
    ats_requests = ATSResumeRequest.objects.filter(seeker=seeker).order_by("-requested_at")
    unlocked_guides = UnlockedVisaGuide.objects.filter(seeker=seeker).select_related("guide")
    ticket_purchases = TicketPurchase.objects.filter(seeker=seeker).select_related("event").order_by("-purchased_at")

    visa_discount = (
        VisaDiscount.objects.filter(seeker=seeker, valid_until__gte=date.today())
        .order_by("-purchased_at")
        .first()
    )

    whatsapp_active, whatsapp_days_left = seeker.whatsapp_recommendation_status()

    can_unlock, cooldown_remaining, cooldown_expires = seeker.can_unlock_exclusive_jobs()
    cooldown_total = 3 * 24 * 60 * 60  # 3 days in seconds
    cooldown_progress = 100.0 * (cooldown_total - cooldown_remaining) / cooldown_total
    cooldown_elapsed = cooldown_total - cooldown_remaining

    unlocked_jobs = UnlockedExclusiveJob.objects.filter(
        seeker=seeker,
        expires_at__gte=now()
    )

    context = {
        "seeker": seeker,
        "applications": applications,
        "ats_requests": ats_requests,
        "visa_discount": visa_discount,
        "unlocked_guides": unlocked_guides,
        "ticket_purchases": ticket_purchases,
        "whatsapp_active": whatsapp_active,
        "whatsapp_days_left": whatsapp_days_left,
        "can_unlock": can_unlock,
        "cooldown_remaining": cooldown_remaining,
        "cooldown_expires": cooldown_expires,
        "cooldown_progress": cooldown_progress,
        "cooldown_elapsed": cooldown_elapsed,
        "unlocked_jobs": unlocked_jobs,
    }

    return render(request, "seeker/dashboard.html", context)



def buy_ats_cv(request):
    """Handles ATS CV purchase using credits."""
    seeker = request.user

    if seeker.credits >= 30:  # Cost of ATS CV
        seeker.credits -= 30
        seeker.save(update_fields=["credits"])

        ats_request = ATSResumeRequest.objects.create(seeker=seeker)
        ats_request.generate_order_id()

        # Email Notification to Seeker (with safety checks)
        if seeker.email:
            try:
                send_mail(
                    subject="📄 ATS CV Order Confirmation",
                    message=(
                        f"Dear {seeker.get_full_name() or seeker.username},\n\n"
                        f"Your ATS CV request has been received!\n"
                        f"Order ID: {ats_request.order_id}\n\n"
                        "Your optimized CV will be delivered within 3 working days.\n\n"
                        "Thank you for using Eurapos!"
                    ),
                    from_email="noreply@eurapos.com",
                    recipient_list=[seeker.email],
                    fail_silently=False,
                )
            except BadHeaderError:
                messages.warning(request, "⚠️ Order placed but email failed due to invalid header.")
                logger.error("BadHeaderError while sending ATS CV confirmation to %s", seeker.email)
            except Exception as e:
                messages.warning(request, "⚠️ Order placed but email notification failed.")
                logger.error("Error sending ATS CV confirmation email: %s", str(e))
        else:
            messages.warning(request, "⚠️ Order placed but email not sent (missing email address).")

        messages.success(
            request,
            f"✅ ATS CV request placed! Order ID: {ats_request.order_id}. "
            "Your CV will be delivered within 3 working days."
        )

    else:
        messages.error(request, "❌ Not enough credits to request an ATS CV.")

    return redirect("seeker:dashboard")


@require_POST
@login_required
def buy_whatsapp_recommendations(request):
    seeker = request.user
    whatsapp_number = request.POST.get("whatsapp_number", "").strip()

    if not whatsapp_number:
        messages.error(request, "Please enter your WhatsApp number.")
        return redirect("seeker:dashboard")

    if seeker.credits >= 20:
        seeker.credits -= 20
        seeker.receive_whatsapp_jobs = True
        seeker.whatsapp_number = whatsapp_number
        seeker.whatsapp_optin_started = now()
        seeker.whatsapp_optin_expires = now() + timedelta(days=10)
        seeker.save(update_fields=[
            "credits", "receive_whatsapp_jobs", "whatsapp_number",
            "whatsapp_optin_started", "whatsapp_optin_expires"
        ])

        send_mail(
            subject="📢 New WhatsApp Job Notification Purchase!",
            message=f"User {seeker.username} ({whatsapp_number}) has purchased WhatsApp job recommendations for 10 days.",
            from_email="noreply@eurapos.com",
            recipient_list=["admin@eurapos.com"],
        )

        messages.success(request, "✅ WhatsApp job notifications enabled for 10 days!")
    else:
        messages.error(request, "❌ Not enough credits to enable WhatsApp job notifications.")

    return redirect("seeker:dashboard")


def buy_visa_discount(request):
    """Handles purchasing visa consultancy discount with credits."""
    seeker = request.user

    if seeker.credits < 40:
        messages.error(request, "Not enough credits to purchase the Visa Consultancy Discount.")
        return redirect("seeker:dashboard")

    # Deduct credits and create discount record
    seeker.credits -= 40
    seeker.save(update_fields=["credits"])

    visa_discount = VisaDiscount.objects.create(seeker=seeker)
    visa_discount.generate_order_id()
    visa_discount.generate_coupon_code()
    visa_discount.set_validity_period(days=30)

    # ✅ Generate a valid PDF file using centralized utility
    pdf_relative_path = generate_visa_discount_pdf(
        seeker=seeker,
        order_id=visa_discount.order_id,
        coupon_code=visa_discount.coupon_code,
        valid_until=visa_discount.valid_until,
        purchased_at=visa_discount.purchased_at
    )

    visa_discount.pdf_file = pdf_relative_path
    visa_discount.save(update_fields=["pdf_file"])

    # ✅ Email Confirmation
    send_mail(
        subject="✅ Visa Consultancy Discount Confirmation",
        message=(
            f"Hi {seeker.username},\n\n"
            f"Your Visa Consultancy Discount is confirmed!\n"
            f"Order ID: {visa_discount.order_id}\n"
            f"Coupon Code: {visa_discount.coupon_code}\n"
            f"Valid Until: {visa_discount.valid_until.strftime('%B %d, %Y')}\n\n"
            f"You can download the confirmation PDF anytime from your dashboard."
        ),
        from_email="noreply@eurapos.com",
        recipient_list=[seeker.email],
    )

    messages.success(request, f"✅ Visa Consultancy Discount purchased! Order ID: {visa_discount.order_id}.")
    return redirect("seeker:dashboard")


def unlock_visa_guide(request, guide_id):
    """Handles Visa Guide unlocking using credits."""
    guide = get_object_or_404(VisaGuide, id=guide_id)
    seeker = request.user

    if seeker.credits >= guide.credits_required:
        seeker.credits -= guide.credits_required
        seeker.save(update_fields=["credits"])

        UnlockedVisaGuide.objects.create(seeker=seeker, guide=guide)

        # Email Notification to Admin
        send_mail(
            subject="📄 New Visa Guide Purchase!",
            message=f"User {seeker.username} purchased the {guide.country} Visa Guide.",
            from_email="noreply@eurapos.com",
            recipient_list=["admin@eurapos.com"],
        )

        messages.success(request, f"✅ You have unlocked the {guide.country} Visa Guide! You can now download it anytime.")
    else:
        messages.error(request, "Not enough credits to unlock this Visa Guide.")

    return redirect("seeker:dashboard")


@login_required
def notifications_page(request):
    seeker = request.user

    notifications = Notification.objects.filter(seeker=seeker).order_by("-created_at")

    context = {
        "notifications": notifications,
    }

    return render(request, "notifications/notifications_page.html", context)


@login_required
def mark_notification_read(request, notification_id):
    note = get_object_or_404(Notification, id=notification_id, seeker=request.user)
    note.read = True
    note.save(update_fields=["read"])
    return redirect("seeker:notifications_page")


@csrf_exempt
@require_POST
def ajax_mark_notification_read(request):
    note_id = request.POST.get("id")
    if not request.user.is_authenticated:
        return JsonResponse({"error": "Unauthorized"}, status=401)

    try:
        note = Notification.objects.get(id=note_id, seeker=request.user)
        note.read = True
        note.save(update_fields=["read"])
        return JsonResponse({"success": True})
    except Notification.DoesNotExist:
        return JsonResponse({"error": "Notification not found"}, status=404)

import os
from django.http import FileResponse, Http404
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404, render
from django.utils.timezone import now
from django.contrib import messages
from adminpanel.utils import notify_admin
from django.core.mail import send_mail
from notifications.models import Notification
from .models import EventTicket, TicketPurchase
from seeker.models import Seeker


def event_list(request):
    """Public list of all upcoming events."""
    events = EventTicket.objects.filter(available_until__gte=now().date()).order_by("available_until")
    return render(request, "events/event_list.html", {"events": events})


def event_detail(request, event_id):
    """Shows detailed view of a specific event."""
    event = get_object_or_404(EventTicket, id=event_id)

    purchased = False
    if request.user.is_authenticated:
        purchased = TicketPurchase.objects.filter(seeker=request.user, event=event).exists()

    return render(request, "events/event_detail.html", {
        "event": event,
        "purchased": purchased
    })


@login_required
def purchase_ticket(request, event_id):
    """Handles event ticket purchases using credits and notifies admin."""
    event = get_object_or_404(EventTicket, id=event_id)
    seeker = request.user

    if TicketPurchase.objects.filter(seeker=seeker, event=event).exists():
        messages.info(request, "🎫 You've already purchased a ticket for this event.")
        return redirect("events:event_detail", event_id=event.id)

    if seeker.credits >= event.credits_required:
        seeker.credits -= event.credits_required
        seeker.save(update_fields=["credits"])

        purchase = TicketPurchase.objects.create(seeker=seeker, event=event)
        purchase.generate_order_id()
        purchase.generate_confirmation_code()

        # ✅ Send email confirmation
        send_mail(
            subject="🎟 Event Ticket Confirmation",
            message=(
                f"Hi {seeker.username},\n\n"
                f"Your ticket for '{event.title}' is confirmed!\n\n"
                f"Order ID: {purchase.order_id}\n"
                f"Confirmation Code: {purchase.confirmation_code}\n\n"
                f"Thank you for booking with Eurapos!"
            ),
            from_email="noreply@eurapos.com",
            recipient_list=[seeker.email],
        )

        # ✅ In-app notification
        Notification.objects.create(
            seeker=seeker,
            message=f"🎟 You purchased a ticket for '{event.title}'. Confirmation Code: {purchase.confirmation_code}"
        )

        # ✅ Admin panel notification
        notify_admin(
            message=f"🎟 Event ticket purchased by {seeker.email} for '{event.title}' "
                    f"(Event ID: {event.id}, Order ID: {purchase.order_id})",
            type="event_ticket"
        )

        messages.success(
            request,
            f"✅ Ticket purchased! Order ID: {purchase.order_id}. Confirmation Code: {purchase.confirmation_code}. "
            "You will receive the ticket within 3 working days."
        )
    else:
        messages.error(request, "❌ Not enough credits to buy this ticket.")

    return redirect("events:event_detail", event_id=event.id)


@login_required
def download_ticket(request, ticket_id):
    """Allows user to download their confirmed, admin-uploaded event ticket PDF."""
    ticket = get_object_or_404(TicketPurchase, id=ticket_id, seeker=request.user)

    if not ticket.confirmed:
        messages.error(request, "❌ This ticket hasn't been marked as delivered yet.")
        return redirect("seeker:dashboard")

    if not ticket.ticket_file:
        messages.error(request, "📄 Ticket file not uploaded yet. Please check back later.")
        return redirect("seeker:dashboard")

    return FileResponse(ticket.ticket_file.open('rb'), as_attachment=True, filename=f"{ticket.event.title}_ticket.pdf")

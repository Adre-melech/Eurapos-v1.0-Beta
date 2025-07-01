from django.shortcuts import get_object_or_404, redirect
from django.contrib.admin.views.decorators import staff_member_required
from django.http import JsonResponse
from seeker.models import Seeker
from .models import Notification
from django.contrib import messages


@staff_member_required
def send_alert(request, seeker_id):
    """Admin sends a popup notification to a logged-in user."""
    seeker = get_object_or_404(Seeker, id=seeker_id)

    if request.method == "POST":
        message = request.POST.get("message", "").strip()
        if not message:
            return JsonResponse({"success": False, "error": "Message cannot be empty."})

        # Create notification
        Notification.objects.create(seeker=seeker, message=message)

        return JsonResponse({"success": True, "message": f"Alert sent to {seeker.username}!"})

    return JsonResponse({"success": False, "error": "Invalid request method."})


def mark_notification_read(request, notification_id):
    """
    Marks a notification as read.
    Only allows the seeker who owns the notification to mark it as read.
    """
    notification = get_object_or_404(Notification, id=notification_id, seeker=request.user)
    if request.method == "POST":
        notification.read = True
        notification.save()
        messages.success(request, "Notification marked as read.")
    return redirect('seeker:dashboard')


from django.db import models
from seeker.models import Seeker
from cloudinary.models import CloudinaryField
import random
import string


class EventTicket(models.Model):
    """Stores event details"""
    title = models.CharField(max_length=200)
    image = CloudinaryField("Event Image", folder="eurapos/events/", blank=True, null=True)
    credits_required = models.PositiveIntegerField()
    available_until = models.DateField()
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.title} ({self.credits_required} Credits)"


class TicketPurchase(models.Model):
    """Tracks ticket purchases & confirmation codes"""
    seeker = models.ForeignKey(Seeker, on_delete=models.CASCADE)
    event = models.ForeignKey(EventTicket, on_delete=models.CASCADE)
    purchased_at = models.DateTimeField(auto_now_add=True)
    order_id = models.CharField(max_length=12, unique=True, blank=True)  # Order tracking ID
    confirmation_code = models.CharField(max_length=12, unique=True, blank=True)  # Ticket confirmation
    confirmed = models.BooleanField(default=False)  # Marked as delivered by admin
    ticket_file = models.FileField(upload_to="event_tickets/", blank=True, null=True)  # Admin-uploaded ticket

    def generate_order_id(self):
        """Generates a unique order ID"""
        if not self.order_id:
            self.order_id = "ORD-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
            self.save(update_fields=["order_id"])

    def generate_confirmation_code(self):
        """Generates a unique confirmation code"""
        if not self.confirmation_code:
            self.confirmation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            self.save(update_fields=["confirmation_code"])

    def save(self, *args, **kwargs):
        is_update = self.pk is not None
        if is_update:
            previous = TicketPurchase.objects.filter(pk=self.pk).values_list("ticket_file", flat=True).first()
            if not previous and self.ticket_file:
                from notifications.models import Notification
                Notification.objects.create(
                    seeker=self.seeker,
                    message=f"🎟️ Your ticket for '{self.event.title}' has been delivered! Check your dashboard."
                )
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Order {self.order_id} - Ticket for {self.event.title} ({self.seeker.username})"
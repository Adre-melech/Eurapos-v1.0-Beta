from django.contrib import admin
from .models import EventTicket, TicketPurchase

@admin.register(EventTicket)
class EventTicketAdmin(admin.ModelAdmin):
    list_display = ("title", "credits_required", "available_until")
    list_filter = ("available_until",)
    search_fields = ("title",)
    ordering = ("available_until",)


@admin.register(TicketPurchase)
class TicketPurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "order_id", "seeker", "event", "purchased_at",
        "confirmation_code", "confirmed", "ticket_file_display"
    )
    list_filter = ("confirmed", "purchased_at", "event")
    search_fields = ("order_id", "seeker__username", "event__title", "confirmation_code")
    readonly_fields = ("order_id", "confirmation_code", "purchased_at")
    fields = (
        "seeker", "event", "order_id", "confirmation_code",
        "confirmed", "ticket_file", "purchased_at"
    )
    actions = ["confirm_selected_tickets"]

    def confirm_selected_tickets(self, request, queryset):
        updated_count = queryset.update(confirmed=True)
        self.message_user(request, f"✅ {updated_count} selected ticket(s) have been confirmed.")

    def ticket_file_display(self, obj):
        if obj.ticket_file:
            return "✅ Uploaded"
        return "—"
    ticket_file_display.short_description = "Ticket File"
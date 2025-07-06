from django.contrib import admin
from .models import PartnerRegistration


@admin.register(PartnerRegistration)
class PartnerRegistrationAdmin(admin.ModelAdmin):
    list_display = ["company", "email", "submitted_at", "is_approved"]
    list_filter = ["is_approved", "submitted_at"]
    search_fields = ["company", "email"]
    ordering = ["-submitted_at"]
    readonly_fields = ["submitted_at"]
    fields = ["company", "email", "submitted_at", "is_approved", "staff_notes"]
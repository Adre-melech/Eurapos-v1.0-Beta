from django.contrib import admin
from import_export.admin import ExportMixin
from .models import PartnerRegistration, ResumeAccessOrder


@admin.register(PartnerRegistration)
class PartnerRegistrationAdmin(admin.ModelAdmin):
    list_display = ["company", "email", "submitted_at", "is_approved"]
    list_filter = ["is_approved", "submitted_at"]
    search_fields = ["company", "email"]
    ordering = ["-submitted_at"]
    readonly_fields = ["submitted_at"]
    fields = ["company", "email", "submitted_at", "is_approved", "staff_notes"]


@admin.register(ResumeAccessOrder)
class ResumeAccessOrderAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("name", "email", "plan", "company_name", "phone", "created_at", "contacted")
    list_filter = ("plan", "contacted")
    search_fields = ("name", "email", "company_name", "phone")
    ordering = ("-created_at",)


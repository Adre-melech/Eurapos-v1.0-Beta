from django.contrib import admin
from home.models import ContactMessage, PolicySection

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at", "responded"]
    search_fields = ["name", "email", "message"]
    list_filter = ["responded", "created_at"]


@admin.register(PolicySection)
class PolicySectionAdmin(admin.ModelAdmin):
    list_display = ("title", "policy_type", "updated_at")
    list_filter = ("policy_type", "updated_at")
    search_fields = ("title", "description")
    ordering = ("-updated_at",)

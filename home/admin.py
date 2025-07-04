from django.contrib import admin
from home.models import ContactMessage

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "created_at", "responded"]
    search_fields = ["name", "email", "message"]
    list_filter = ["responded", "created_at"]
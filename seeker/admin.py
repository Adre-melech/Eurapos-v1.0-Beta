from django.contrib import admin
from django.utils.timezone import now
from import_export.admin import ExportMixin
from notifications.models import Notification
from .models import Seeker, ATSResumeRequest, VisaDiscount, VisaGuide, UnlockedVisaGuide, ConsentLog, UserActivity, SuspiciousLoginAlert


# === Seeker Admin ===
class SeekerAdmin(ExportMixin, admin.ModelAdmin):
    list_display = (
        "seeker_id", "username", "email", "phone", "country",
        "job_title", "date_joined", "credits",
        "receive_whatsapp_jobs", "whatsapp_optin_started", "whatsapp_optin_expires",
        "consent_accepted", "consent_accepted_at", "timezone"
    )
    search_fields = ("username", "email", "seeker_id")
    list_filter = (
        "country", "job_title", "date_joined", "receive_whatsapp_jobs",
        "consent_accepted", "timezone"
    )
    actions = ["disable_expired_whatsapp_optins"]

    def disable_expired_whatsapp_optins(self, request, queryset):
        updated = 0
        for seeker in queryset:
            if seeker.whatsapp_optin_expires and seeker.whatsapp_optin_expires < now().date():
                seeker.receive_whatsapp_jobs = False
                seeker.whatsapp_optin_expires = None
                seeker.save(update_fields=["receive_whatsapp_jobs", "whatsapp_optin_expires"])
                updated += 1
        self.message_user(request, f"✅ Disabled expired WhatsApp opt-ins for {updated} seeker(s).")

    def save_model(self, request, obj, form, change):
        if change:
            old_obj = Seeker.objects.get(pk=obj.pk)
            if obj.credits > old_obj.credits:
                added = obj.credits - old_obj.credits
                Notification.objects.create(
                    seeker=obj,
                    message=f"🎁 You've been rewarded with {added} bonus credit(s) by EURAPOS!"
                )
        super().save_model(request, obj, form, change)

# === ConsentLog Admin ===
class ConsentLogAdmin(ExportMixin, admin.ModelAdmin):
    list_display = ("ip_address", "timezone", "accepted_at")
    list_filter = ("timezone", "accepted_at")
    search_fields = ("ip_address", "timezone")
    ordering = ("-accepted_at",)


class ATSResumeRequestAdmin(admin.ModelAdmin):
    list_display = ("order_id", "seeker", "requested_at", "processed", "cv_file_link")
    list_filter = ("processed", "requested_at")
    search_fields = ("order_id", "seeker__username", "seeker__email")
    readonly_fields = ("order_id", "requested_at")
    fields = ("seeker", "order_id", "requested_at", "processed", "cv_file")
    actions = ["mark_as_processed"]

    def mark_as_processed(self, request, queryset):
        updated = queryset.update(processed=True)
        self.message_user(request, f"✅ Marked {updated} request(s) as processed.")

    def cv_file_link(self, obj):
        if obj.cv_file:
            return f"<a href='{obj.cv_file.url}' target='_blank'>📄 View CV</a>"
        return "—"
    cv_file_link.allow_tags = True
    cv_file_link.short_description = "CV File"

class VisaDiscountAdmin(admin.ModelAdmin):
    list_display = ("seeker", "order_id", "coupon_code", "valid_until", "purchased_at")
    search_fields = ("order_id", "coupon_code", "seeker__username", "seeker__email")
    list_filter = ("valid_until", "purchased_at")


class VisaGuideAdmin(admin.ModelAdmin):
    list_display = ("country", "credits_required")
    search_fields = ("country",)


class UserActivityAdmin(admin.ModelAdmin):
    list_display = (
        "ip_address",
        "user_display",
        "session_key",
        "path",
        "method",
        "timestamp",
    )
    list_filter = ("method", "timestamp")
    search_fields = ("user__username", "session_key", "path", "ip_address", "user_agent", "referrer")
    readonly_fields = ("user", "session_key", "path", "method", "timestamp", "ip_address", "user_agent", "referrer")
    ordering = ("-timestamp",)

    def user_display(self, obj):
        return obj.user.username if obj.user else "Anonymous"
    user_display.short_description = "User"




admin.site.register(VisaGuide, VisaGuideAdmin)
admin.site.register(VisaDiscount, VisaDiscountAdmin)
admin.site.register(ATSResumeRequest, ATSResumeRequestAdmin)
admin.site.register(Seeker, SeekerAdmin)
admin.site.register(ConsentLog, ConsentLogAdmin)
admin.site.register(UserActivity, UserActivityAdmin)
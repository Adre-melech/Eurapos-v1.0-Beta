from django.contrib import admin
from django.utils.timezone import now
from notifications.models import Notification
from .models import Seeker, ATSResumeRequest, VisaDiscount, VisaGuide


class SeekerAdmin(admin.ModelAdmin):
    list_display = (
        'seeker_id', 'username', 'email', 'phone', 'country',
        'job_title', 'date_joined', 'credits',
        'receive_whatsapp_jobs', 'whatsapp_optin_started', 'whatsapp_optin_expires'
    )
    search_fields = ('username', 'email', 'seeker_id')
    list_filter = ('country', 'job_title', 'date_joined', 'receive_whatsapp_jobs')

    actions = ["disable_expired_whatsapp_optins"]

    def disable_expired_whatsapp_optins(self, request, queryset):
        """Bulk action to disable expired WhatsApp notifications."""
        updated = 0
        for seeker in queryset:
            if seeker.whatsapp_optin_expires and seeker.whatsapp_optin_expires < now().date():
                seeker.receive_whatsapp_jobs = False
                seeker.whatsapp_optin_expires = None
                seeker.save(update_fields=["receive_whatsapp_jobs", "whatsapp_optin_expires"])
                updated += 1
        self.message_user(request, f"✅ Disabled expired WhatsApp opt-ins for {updated} seeker(s).")

    def save_model(self, request, obj, form, change):
        """Send a notification if admin increased seeker's credits."""
        if change:
            old_obj = Seeker.objects.get(pk=obj.pk)
            if obj.credits > old_obj.credits:
                added = obj.credits - old_obj.credits
                Notification.objects.create(
                    seeker=obj,
                    message=f"🎁 You've been rewarded with {added} bonus credit(s) by EURAPOS!"
                )
        super().save_model(request, obj, form, change)


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


admin.site.register(VisaGuide, VisaGuideAdmin)
admin.site.register(VisaDiscount, VisaDiscountAdmin)
admin.site.register(ATSResumeRequest, ATSResumeRequestAdmin)
admin.site.register(Seeker, SeekerAdmin)
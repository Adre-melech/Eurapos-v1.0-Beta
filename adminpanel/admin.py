from django.contrib import admin
from jobs.models import JobPost, Application, JobCountry, Category, SeekerCountry
from seeker.models import Seeker
from django.utils.html import format_html
from notifications.models import Notification


class JobPostAdmin(admin.ModelAdmin):
    list_display = (
        'job_id',
        'title',
        'company_name',
        'deadline',
        'category',
        'country',
        'views',
        'image_preview'
    )
    search_fields = ('title', 'company_name', 'job_id')
    list_filter = ('category', 'country')
    readonly_fields = ('views',)

    fields = (
        'image',
        'image_alt',
        'title',
        'company_name',
        'salary',
        'deadline',
        'Overview',
        'responsibilities',
        'requirements',
        'country',
        'category',
        'exclusive_job',
        'hr_name',
        'hr_phone',
        'hr_email',
        'views',
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-height: 60px;" />', obj.image.url)
        return "No Image"

    image_preview.short_description = "Image"


class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('seeker', 'job', 'status', 'applied_at')
    search_fields = ('seeker__username', 'job__title')
    list_filter = ('status',)
    actions = ['update_status_to_review', 'update_status_to_selected', 'update_status_to_rejected']

    def update_status_to_review(self, request, queryset):
        queryset.update(status='Under Review')
        self.message_user(request, "Selected applications marked as 'Under Review'.")

    def update_status_to_selected(self, request, queryset):
        queryset.update(status='Selected')
        self.message_user(request, "Selected applications marked as 'Selected'.")

    def update_status_to_rejected(self, request, queryset):
        queryset.update(status='Rejected')
        self.message_user(request, "Selected applications marked as 'Rejected'.")


class SeekerAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'country', 'phone')
    search_fields = ('username', 'email', 'phone')


class JobCountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class SeekerCountryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ('seeker', 'message', 'created_at', 'read')
    list_filter = ('read',)


# Register models with admin panel
admin.site.register(JobPost, JobPostAdmin)
admin.site.register(Application, ApplicationAdmin)
admin.site.register(JobCountry)
admin.site.register(SeekerCountry)
admin.site.register(Category)
admin.site.register(Notification, NotificationAdmin)
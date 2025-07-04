from django.contrib import admin
from .models import JobPost, Application, JobCountry, SeekerCountry, JobTitle, Category, UnlockedExclusiveJob


class JobTitleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class UnlockedExclusiveJobAdmin(admin.ModelAdmin):
    list_display = ("seeker", "job", "expires_at")
    list_filter = ("job__category", "expires_at")
    search_fields = ("seeker__username", "job__title")


# Register models with admin panel
admin.site.register(JobTitle, JobTitleAdmin)
admin.site.register(UnlockedExclusiveJob, UnlockedExclusiveJobAdmin)
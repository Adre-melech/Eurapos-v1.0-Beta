from django.contrib import admin
from .models import JobPost, Application, JobCountry, SeekerCountry, JobTitle, Category


class JobTitleAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# Register models with admin panel
admin.site.register(JobTitle, JobTitleAdmin)
from django.urls import path
from recruiter import views

app_name = "recruiter"

urlpatterns = [
    path("why-partner/", views.why_partner, name="why_partner"),
    path("resume-access/", views.resume_access, name="resume_access"),
    path("workforce-solutions/", views.workforce_solutions, name="workforce_solutions"),
    path("post-jobs/", views.post_jobs, name="post_jobs"),
    path("partner-register/", views.partner_register, name="partner_register"),
]
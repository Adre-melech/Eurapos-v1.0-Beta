from django.urls import path
from .views import (
    job_list, job_detail, rate_application, apply_job, ajax_search,
    unlock_hr_info, unlock_exclusive_jobs, near_deadline_jobs, hot_jobs,
    all_jobs, load_more_jobs, load_more_near_deadline_jobs, ajax_near_deadline_search,
    ajax_all_jobs_search, load_more_hot_jobs, ajax_hot_jobs_search, buy_priority_review, exclusive_jobs,
    recommended_jobs
)

app_name = "jobs"

urlpatterns = [
    path("", job_list, name="job_list"),  # Job browsing page
    path("ajax/filter/", job_list, name="job_filter_ajax"),  # AJAX filtering for jobs

    path("all-jobs/", all_jobs, name="all_jobs"),
    path("load-more-jobs/", load_more_jobs, name="load_more_jobs"),
    path("ajax-all-jobs-search/", ajax_all_jobs_search, name="ajax_all_jobs_search"),

    path("near-deadline-jobs/", near_deadline_jobs, name="near_deadline_jobs"),
    path("load-more-near-deadline-jobs/", load_more_near_deadline_jobs, name="load_more_near_deadline_jobs"),
    path("ajax-near-deadline-search/", ajax_near_deadline_search, name="ajax_near_deadline_search"),

    path("hot-jobs/", hot_jobs, name="hot_jobs"),
    path("load-more-hot-jobs/", load_more_hot_jobs, name="load_more_hot_jobs"),
    path("ajax-hot-jobs-search/", ajax_hot_jobs_search, name="ajax_hot_jobs_search"),

    path("ajax_search/", ajax_search, name="ajax_search"),

    path("<int:job_id>/", job_detail, name="job_detail"),
    path("<int:job_id>/apply/", apply_job, name="apply_job"),
    path("rate/<int:application_id>/", rate_application, name="rate_application"),

    path("unlock_hr_info/<int:job_id>/", unlock_hr_info, name="unlock_hr_info"),
    path("unlock_exclusive_jobs/", unlock_exclusive_jobs, name="unlock_exclusive_jobs"),
    path("exclusive-jobs/", exclusive_jobs, name="exclusive_jobs"),

    path("recommended/", recommended_jobs, name="recommended_jobs"),



    path("buy_priority_review/<int:application_id>/", buy_priority_review, name="buy_priority_review"),
]

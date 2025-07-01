from django.urls import path
from .views import (
    admin_dashboard, admin_login, admin_logout,
    add_job, manage_jobs, delete_job, edit_job,
    add_category, manage_categories, edit_category, delete_category,
    add_job_title, manage_job_titles, edit_job_title, delete_job_title,
    add_seeker_country, manage_seeker_countries, edit_seeker_country, delete_seeker_country,
    add_job_country, manage_job_countries, edit_job_country, delete_job_country,
    manage_seeker, update_application_status, delete_seeker, manage_credits, upload_ats_cv, manage_all_seekers,

    # Event Management
    add_event, manage_events, edit_event, delete_event,

    # Visa Guide Management
    add_visa_guide, manage_visa_guides, edit_visa_guide, delete_visa_guide,

    # Ticket Management
    mark_ticket_delivered,

    # ATS Management
    mark_ats_processed, upload_event_ticket, confirm_event_ticket, mark_priority_done, all_applications,
    priority_applications_list, whatsapp_subscribers_list, ats_requests_list, delivered_ats_resumes_list,
    all_pending_event_tickets, delivered_event_tickets, unlocked_access_users
)

app_name = "adminpanel"

urlpatterns = [
    # Admin Authentication
    path("", admin_login, name="admin_login"),
    path("dashboard/", admin_dashboard, name="admin_dashboard"),
    path("logout/", admin_logout, name="admin_logout"),

    path("unlocked-access/", unlocked_access_users, name="unlocked_access_users"),

    # Applications
    path("applications/", all_applications, name="all_applications"),

    # Job Management
    path("add-job/", add_job, name="add_job"),
    path("manage-jobs/", manage_jobs, name="manage_jobs"),
    path("edit-job/<int:job_id>/", edit_job, name="edit_job"),
    path("delete-job/<int:job_id>/", delete_job, name="delete_job"),

    # Categories Management
    path("add-category/", add_category, name="add_category"),
    path("manage-categories/", manage_categories, name="manage_categories"),
    path("edit-category/<int:category_id>/", edit_category, name="edit_category"),
    path("delete-category/<int:category_id>/", delete_category, name="delete_category"),

    # Job Titles Management
    path("add-job-title/", add_job_title, name="add_job_title"),
    path("manage-job-titles/", manage_job_titles, name="manage_job_titles"),
    path("edit-job-title/<int:job_title_id>/", edit_job_title, name="edit_job_title"),
    path("delete-job-title/<int:job_title_id>/", delete_job_title, name="delete_job_title"),

    # Seeker Countries Management
    path("add-seeker-country/", add_seeker_country, name="add_seeker_country"),
    path("manage-seeker-countries/", manage_seeker_countries, name="manage_seeker_countries"),
    path("edit-seeker-country/<int:country_id>/", edit_seeker_country, name="edit_seeker_country"),
    path("delete-seeker-country/<int:country_id>/", delete_seeker_country, name="delete_seeker_country"),

    # Job Countries Management
    path("add-job-country/", add_job_country, name="add_job_country"),
    path("manage-job-countries/", manage_job_countries, name="manage_job_countries"),
    path("edit-job-country/<int:country_id>/", edit_job_country, name="edit_job_country"),
    path("delete-job-country/<int:country_id>/", delete_job_country, name="delete_job_country"),

    # Seeker Management
    path("update-application-status/<int:application_id>/", update_application_status, name="update_application_status"),
    path("edit-seeker/<int:seeker_id>/", manage_seeker, name="edit_seeker"),
    path("delete-seeker/<int:seeker_id>/", delete_seeker, name="delete_seeker"),
    path("seekers/manage/", manage_all_seekers, name="manage_all_seekers"),

    # Applications & Credits Management
    path("update-application-status/<int:application_id>/", update_application_status, name="update_application_status"),
    path("manage-credits/<int:seeker_id>/", manage_credits, name="manage_credits"),

    # Event Management
    path("add-event/", add_event, name="add_event"),
    path("manage-events/", manage_events, name="manage_events"),
    path("edit-event/<int:event_id>/", edit_event, name="edit_event"),
    path("delete-event/<int:event_id>/", delete_event, name="delete_event"),

    # Visa Guide Management
    path("add-visa-guide/", add_visa_guide, name="add_visa_guide"),
    path("manage-visa-guides/", manage_visa_guides, name="manage_visa_guides"),
    path("edit-visa-guide/<int:visa_guide_id>/", edit_visa_guide, name="edit_visa_guide"),
    path("delete-visa-guide/<int:visa_guide_id>/", delete_visa_guide, name="delete_visa_guide"),

    path("ticket/<int:ticket_id>/mark-delivered/", mark_ticket_delivered, name="mark_ticket_delivered"),

    path("ats-requests/", ats_requests_list, name="ats_requests_list"),
    path("ats-request/<int:request_id>/mark-processed/", mark_ats_processed, name="mark_ats_processed"),
    path("ats-request/<int:request_id>/upload/", upload_ats_cv, name="upload_ats_cv"),
    path("ats/delivered/", delivered_ats_resumes_list, name="delivered_ats_resumes"),

    path('pending-tickets/', all_pending_event_tickets, name='pending_tickets_list'),
    path('event-ticket/upload/<int:ticket_id>/', upload_event_ticket, name='upload_event_ticket'),
    path('event-ticket/confirm/<int:ticket_id>/', confirm_event_ticket, name='confirm_event_ticket'),
    path("event-tickets/delivered/", delivered_event_tickets, name="delivered_event_tickets"),

    path('priority-applications/', priority_applications_list, name='priority_applications_list'),
    path('whatsapp-subscribers/', whatsapp_subscribers_list, name='whatsapp_subscribers_list'),
    path('priority-application/done/<int:app_id>/', mark_priority_done, name='mark_priority_done'),
]
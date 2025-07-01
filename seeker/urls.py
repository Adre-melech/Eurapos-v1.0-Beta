from django.urls import path
from .views import seeker_register, seeker_login, seeker_logout, seeker_dashboard, buy_whatsapp_recommendations, \
    buy_visa_discount, unlock_visa_guide, buy_ats_cv, notifications_page, ajax_mark_notification_read
from notifications.views import mark_notification_read

app_name = "seeker"

urlpatterns = [
    path("register/", seeker_register, name="seeker_register"),
    path("login/", seeker_login, name="seeker_login"),
    path("logout/", seeker_logout, name="seeker_logout"),
    path("dashboard/", seeker_dashboard, name="dashboard"),  # Seeker application tracking
    path('notifications/mark_read/<int:notification_id>/', mark_notification_read, name='mark_notification_read'),
    path("buy-ats-cv/", buy_ats_cv, name="buy_ats_cv"),
    path("buy-whatsapp-recommendations/", buy_whatsapp_recommendations, name="buy_whatsapp_recommendations"),
    path("buy-visa-discount/", buy_visa_discount, name="buy_visa_discount"),
    path("visa-guide/unlock/<int:guide_id>/", unlock_visa_guide, name="unlock_visa_guide"),
    path("all/", notifications_page, name="notifications_page"),
    path("notification/read/<int:notification_id>/", mark_notification_read, name="mark_notification_read"),
    path("ajax/notification/read/", ajax_mark_notification_read, name="ajax_mark_notification_read"),
]

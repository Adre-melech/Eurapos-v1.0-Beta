from django.urls import path, reverse_lazy
from .views import seeker_register, seeker_login, seeker_logout, seeker_dashboard, buy_whatsapp_recommendations, \
    buy_visa_discount, unlock_visa_guide, buy_ats_cv, notifications_page, ajax_mark_notification_read, \
    custom_password_reset_view, rewards_view
from notifications.views import mark_notification_read
from django.contrib.auth import views as auth_views

app_name = "seeker"

urlpatterns = [
    path("register/", seeker_register, name="seeker_register"),
    path("login/", seeker_login, name="seeker_login"),

    path('password-reset/', custom_password_reset_view, name='password_reset'),

    # Needed after form submits
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='seeker/password_reset_done.html'
    ), name='password_reset_done'),

    # ✅ Needed for email link
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='seeker/password_reset_confirm.html',
        success_url=reverse_lazy('seeker:password_reset_complete')
    ), name='password_reset_confirm'),

    # Final message after password reset
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(
        template_name='seeker/password_reset_complete.html'
    ), name='password_reset_complete'),

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
    path("rewards/", rewards_view, name="rewards"),
]

from django.urls import path
from .views import send_alert

app_name = "notifications"

urlpatterns = [
    path("send-alert/<int:seeker_id>/", send_alert, name="send_alert"),
]

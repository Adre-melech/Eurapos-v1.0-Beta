from django.urls import path
from . import views

app_name = "events"

urlpatterns = [
    path("", views.event_list, name="all_events"),                  # All upcoming events
    path("<int:event_id>/", views.event_detail, name="event_detail"),  # Detail view for a single event
    path("<int:event_id>/purchase/", views.purchase_ticket, name="purchase_ticket"),  # Ticket purchase
    path("ticket/<int:ticket_id>/download/", views.download_ticket, name="download_ticket"),
]
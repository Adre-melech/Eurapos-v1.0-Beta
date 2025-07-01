from django.urls import path
from .views import homepage, visa_guides_page

app_name = 'home'

urlpatterns = [
    path('', homepage, name='home'),
    path('visa_guides/', visa_guides_page, name='visa_guides'),
]
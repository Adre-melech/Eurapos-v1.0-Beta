from django.urls import path
from .views import homepage, visa_guides_page, terms_view, privacy_view, about_us, faq, contact_us, send_contact, rewards

app_name = 'home'

urlpatterns = [
    path('', homepage, name='home'),
    path('visa_guides/', visa_guides_page, name='visa_guides'),
    path("terms-&-conditions/", terms_view, name="terms"),
    path("privacy-policy/", privacy_view, name="privacy"),
    path("about-us/", about_us, name="about"),
    path("contact-us/", contact_us, name="contact"),
    path("rewards/", rewards, name="rewards"),
    path("send-contact/", send_contact, name="send_contact"),
    path("faq/", faq, name="faq"),
]
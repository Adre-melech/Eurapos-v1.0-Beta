from django.core.mail import send_mail
from twilio.rest import Client
from django.conf import settings

def send_email_alert(seeker, message):
    """Sends email alert to the seeker"""
    send_mail(
        subject="Eurapos Job Alert",
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[seeker.email],
    )

def send_sms_alert(seeker, message):
    """Sends SMS alert using Twilio"""
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=settings.TWILIO_PHONE_NUMBER,
        to=seeker.phone,
    )
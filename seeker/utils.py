import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4


def generate_visa_discount_pdf(seeker, order_id, coupon_code, valid_until, purchased_at):
    """Generates a styled Visa Discount confirmation PDF and returns the relative path."""
    filename = f"{order_id}.pdf"
    folder_path = os.path.join(settings.MEDIA_ROOT, "visa_discount_pdfs")
    os.makedirs(folder_path, exist_ok=True)
    full_path = os.path.join(folder_path, filename)

    # Create the PDF
    c = canvas.Canvas(full_path, pagesize=A4)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 800, "🎫 Visa Consultancy Discount Confirmation")

    c.setFont("Helvetica", 12)
    c.drawString(72, 770, f"Name: {seeker.username}")
    c.drawString(72, 750, f"Order ID: {order_id}")
    c.drawString(72, 730, f"Coupon Code: {coupon_code}")
    c.drawString(72, 710, f"Valid Until: {valid_until.strftime('%B %d, %Y')}")
    c.drawString(72, 690, f"Redeemed On: {purchased_at.strftime('%B %d, %Y')}")
    c.drawString(72, 660, "📌 Present this PDF to participating consultancies for 10% off.")

    c.showPage()
    c.save()

    return f"visa_discount_pdfs/{filename}"
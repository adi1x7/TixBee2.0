import smtplib
from email.message import EmailMessage

from app.core.config import get_settings


def send_ticket_confirmation(*, recipient: str, visitor_name: str, attraction_name: str, booking_reference: str, ticket_code: str, amount: int) -> str:
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        return "NOT_CONFIGURED"
    message = EmailMessage()
    message["Subject"] = f"Your TixBee ticket · {booking_reference}"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(f"Hi {visitor_name},\n\nYour TixBee booking is confirmed for {attraction_name}.\nTicket: {ticket_code}\nBooking: {booking_reference}\nAmount: ₹{amount}\n\nKeep this ticket code handy at entry.\n\nTixBee")
    message.add_alternative(f"""<html><body style='font-family:Arial;color:#132c3a'><div style='max-width:560px;margin:auto;padding:32px;background:#fffaf1'><p style='color:#e36936;font-size:12px;font-weight:bold'>TIXBEE · VISIT CONFIRMED</p><h1 style='font-family:Georgia'>Your day out is booked.</h1><p>Hi {visitor_name}, your visit to <strong>{attraction_name}</strong> is confirmed.</p><div style='background:#132c3a;color:white;padding:20px;margin:24px 0'><small>TICKET CODE</small><h2>{ticket_code}</h2><p>Booking {booking_reference} · ₹{amount}</p></div><p>Keep this code ready at entry. We look forward to welcoming you.</p></div></body></html>""", subtype="html")
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            smtp.starttls(); smtp.login(settings.smtp_username, settings.smtp_password); smtp.send_message(message)
        return "SENT"
    except Exception:
        return "FAILED"

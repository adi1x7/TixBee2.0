import smtplib
from io import BytesIO
from email.message import EmailMessage
from html import escape

import qrcode

from app.core.config import get_settings


def send_ticket_confirmation(
    *,
    recipient: str,
    visitor_name: str,
    attraction_name: str,
    booking_reference: str,
    ticket_code: str,
    amount: int,
    visit_date: str,
    visit_slot: str,
    quantities: list[tuple[str, int]],
    qr_payload: str,
) -> str:
    """Email a complete ticket receipt with an inline QR for the signed payload."""
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        return "NOT_CONFIGURED"
    message = EmailMessage()
    message["Subject"] = f"Your TixBee ticket · {booking_reference}"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    quantity_text = ", ".join(f"{quantity} {label}" for label, quantity in quantities)
    message.set_content(
        f"Hi {visitor_name},\n\nYour TixBee booking is confirmed.\n\n"
        f"Site: {attraction_name}\nVisit date: {visit_date}\nVisit slot: {visit_slot}\n"
        f"Visitors: {quantity_text}\nAmount paid: ₹{amount}\nTicket ID: {ticket_code}\n"
        f"Booking reference: {booking_reference}\n\n"
        "Your signed QR ticket is included with this email. Keep it ready at entry.\n\nTixBee"
    )
    safe_name = escape(visitor_name)
    safe_site = escape(attraction_name)
    safe_date = escape(visit_date)
    safe_slot = escape(visit_slot)
    safe_ticket = escape(ticket_code)
    safe_reference = escape(booking_reference)
    safe_quantities = escape(quantity_text)
    message.add_alternative(
        f"""<html><body style='font-family:Arial;color:#132c3a'><div style='max-width:560px;margin:auto;padding:32px;background:#fffaf1'><p style='color:#e36936;font-size:12px;font-weight:bold'>TIXBEE · VISIT CONFIRMED</p><h1 style='font-family:Georgia'>Your day out is booked.</h1><p>Hi {safe_name}, your visit to <strong>{safe_site}</strong> is confirmed.</p><div style='background:#132c3a;color:white;padding:20px;margin:24px 0'><small>TICKET ID</small><h2 style='margin:7px 0'>{safe_ticket}</h2><p style='margin:0'>Booking {safe_reference}</p></div><table style='width:100%;border-collapse:collapse;margin:20px 0'><tr><td style='padding:9px 0;color:#586767'>Site</td><td style='padding:9px 0;font-weight:bold'>{safe_site}</td></tr><tr><td style='padding:9px 0;color:#586767'>Visit date</td><td style='padding:9px 0;font-weight:bold'>{safe_date}</td></tr><tr><td style='padding:9px 0;color:#586767'>Visit slot</td><td style='padding:9px 0;font-weight:bold'>{safe_slot}</td></tr><tr><td style='padding:9px 0;color:#586767'>Visitors</td><td style='padding:9px 0;font-weight:bold'>{safe_quantities}</td></tr><tr><td style='padding:9px 0;color:#586767'>Amount paid</td><td style='padding:9px 0;font-weight:bold'>₹{amount}</td></tr></table><div style='text-align:center;margin:28px 0'><img src='cid:tixbee-ticket-qr' width='180' height='180' alt='Signed TixBee ticket QR code' style='display:inline-block;background:#fff;padding:10px'><p style='font-size:12px;color:#586767'>Present this signed QR code at entry.</p></div></div></body></html>""",
        subtype="html",
    )
    qr_stream = BytesIO()
    qrcode.make(qr_payload).save(qr_stream, format="PNG")
    message.get_payload()[-1].add_related(
        qr_stream.getvalue(), maintype="image", subtype="png", cid="<tixbee-ticket-qr>", filename="tixbee-ticket-qr.png"
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            smtp.starttls(); smtp.login(settings.smtp_username, settings.smtp_password); smtp.send_message(message)
        return "SENT"
    except Exception:
        return "FAILED"


def send_password_reset_email(*, recipient: str, visitor_name: str, reset_url: str) -> str:
    """Send a short-lived reset link without logging or persisting its raw token."""
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        return "NOT_CONFIGURED"
    message = EmailMessage()
    message["Subject"] = "Reset your TixBee password"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        f"Hi {visitor_name},\n\nUse this link to reset your TixBee password: {reset_url}\n\n"
        "The link expires in 15 minutes and can be used once. If you did not request it, no action is needed.\n\nTixBee"
    )
    safe_name = escape(visitor_name)
    safe_url = escape(reset_url, quote=True)
    message.add_alternative(
        f"""<html><body style='font-family:Arial;color:#132c3a'><div style='max-width:560px;margin:auto;padding:32px;background:#fffaf1'><p style='color:#e36936;font-size:12px;font-weight:bold'>TIXBEE · ACCOUNT SECURITY</p><h1 style='font-family:Georgia'>Reset your password.</h1><p>Hi {safe_name}, use the secure button below to choose a new password.</p><p style='margin:28px 0'><a href='{safe_url}' style='display:inline-block;background:#e36936;color:#fff;padding:14px 18px;text-decoration:none;font-weight:bold'>Reset password</a></p><p>This link expires in 15 minutes and can be used once. If you did not request it, no action is needed.</p></div></body></html>""",
        subtype="html",
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            smtp.starttls(); smtp.login(settings.smtp_username, settings.smtp_password); smtp.send_message(message)
        return "SENT"
    except Exception:
        return "FAILED"


def send_cancellation_confirmation(
    *, recipient: str, visitor_name: str, attraction_name: str, visit_date: str,
    visit_slot: str, ticket_code: str, refund_amount: int,
) -> str:
    settings = get_settings()
    if not all([settings.smtp_host, settings.smtp_username, settings.smtp_password, settings.smtp_from]):
        return "NOT_CONFIGURED"
    message = EmailMessage()
    message["Subject"] = f"Your TixBee visit has been cancelled · {ticket_code}"
    message["From"] = settings.smtp_from
    message["To"] = recipient
    message.set_content(
        f"Hi {visitor_name},\n\nYour visit has been cancelled.\n\nSite: {attraction_name}\n"
        f"Visit date: {visit_date}\nVisit slot: {visit_slot}\nTicket ID: {ticket_code}\n\n"
        f"₹{refund_amount} will be refunded after deductions to the same payment mode used for the booking.\n\nTixBee"
    )
    message.add_alternative(
        f"""<html><body style='font-family:Arial;color:#132c3a'><div style='max-width:560px;margin:auto;padding:32px;background:#fffaf1'><p style='color:#e36936;font-size:12px;font-weight:bold'>TIXBEE · VISIT CANCELLED</p><h1 style='font-family:Georgia'>Your visit has been cancelled.</h1><p>Hi {escape(visitor_name)}, the following visit is cancelled.</p><table style='width:100%;border-collapse:collapse;margin:22px 0'><tr><td style='padding:9px 0;color:#586767'>Site</td><td style='padding:9px 0;font-weight:bold'>{escape(attraction_name)}</td></tr><tr><td style='padding:9px 0;color:#586767'>Visit date</td><td style='padding:9px 0;font-weight:bold'>{escape(visit_date)}</td></tr><tr><td style='padding:9px 0;color:#586767'>Visit slot</td><td style='padding:9px 0;font-weight:bold'>{escape(visit_slot)}</td></tr><tr><td style='padding:9px 0;color:#586767'>Ticket ID</td><td style='padding:9px 0;font-weight:bold'>{escape(ticket_code)}</td></tr></table><div style='background:#132c3a;color:#fff;padding:20px'><small>REFUND AMOUNT</small><h2 style='margin:7px 0'>₹{refund_amount}</h2><p style='margin:0'>Refunded after deductions to the same payment mode used for the booking.</p></div></div></body></html>""",
        subtype="html",
    )
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=12) as smtp:
            smtp.starttls(); smtp.login(settings.smtp_username, settings.smtp_password); smtp.send_message(message)
        return "SENT"
    except Exception:
        return "FAILED"

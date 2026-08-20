"""
Email sending service using Python standard library smtplib.
Sends rich HTML & plain text password reset emails via SMTP (e.g. Gmail).
"""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from core.config import get_settings

logger = logging.getLogger(__name__)


def send_reset_password_email(email_to: str, reset_link: str) -> bool:
    """
    Send a password reset email to `email_to`.
    Returns True if successfully dispatched via SMTP, False otherwise.
    """
    settings = get_settings()

    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    from_email = settings.EMAILS_FROM_EMAIL or smtp_user or "noreply@plagiarism-ai.com"
    from_name = settings.EMAILS_FROM_NAME

    if not smtp_user or not smtp_password:
        logger.warning(
            f"SMTP_USER/SMTP_PASSWORD not set in environment. "
            f"Skipping SMTP email dispatch to {email_to}. Reset link logged: {reset_link}"
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Password Reset Request — PlagiarismAI"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = email_to

        text_content = f"""
Hello,

You requested a password reset for your PlagiarismAI account.
Click the link below to set a new password (valid for 15 minutes):

{reset_link}

If you did not request this reset, please ignore this email.

Best regards,
PlagiarismAI Support Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
    .header {{ text-align: center; margin-bottom: 24px; }}
    .title {{ font-size: 24px; font-weight: 700; color: #4f46e5; margin: 0 0 4px 0; }}
    .subtitle {{ font-size: 13px; color: #64748b; margin: 0; text-transform: uppercase; letter-spacing: 0.5px; }}
    .body-text {{ font-size: 15px; line-height: 1.6; color: #334155; margin-bottom: 20px; }}
    .btn-wrap {{ text-align: center; margin: 28px 0; }}
    .btn {{ background-color: #4f46e5; color: #ffffff !important; font-weight: 600; text-decoration: none; padding: 14px 28px; border-radius: 8px; display: inline-block; font-size: 15px; box-shadow: 0 4px 12px rgba(79, 70, 229, 0.25); }}
    .link-box {{ font-size: 12px; word-break: break-all; color: #64748b; background: #f8fafc; border: 1px solid #e2e8f0; padding: 12px; border-radius: 6px; margin-top: 24px; }}
    .footer {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2 class="title">PlagiarismAI</h2>
      <p class="subtitle">Assignment Evaluation & Analytics</p>
    </div>
    <div class="body-text">
      <p>Hello,</p>
      <p>We received a request to reset the password for your <strong>PlagiarismAI</strong> account.</p>
      <p>Click the button below to reset your password. This link is valid for <strong>15 minutes</strong>.</p>
    </div>
    <div class="btn-wrap">
      <a href="{reset_link}" class="btn" target="_blank">Reset Password</a>
    </div>
    <div class="body-text">
      <p>If you didn't request a password reset, you can safely ignore this email.</p>
    </div>
    <div class="link-box">
      If the button above doesn't work, copy and paste this link into your web browser:<br>
      <a href="{reset_link}" style="color: #4f46e5;">{reset_link}</a>
    </div>
    <div class="footer">
      &copy; PlagiarismAI. All rights reserved.
    </div>
  </div>
</body>
</html>
"""

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        server = smtplib.SMTP(smtp_host, smtp_port, timeout=12)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(from_email, [email_to], msg.as_string())
        server.quit()

        logger.info(f"✅ Real password reset email successfully sent to {email_to} via SMTP.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send SMTP email to {email_to}: {e}")
        return False

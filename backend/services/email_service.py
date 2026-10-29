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
        logger.info(
            f"SMTP credentials not configured. Skipping SMTP email dispatch to {email_to}. "
            f"Set SMTP_USER and SMTP_PASSWORD in .env for production email delivery."
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


def send_password_changed_notification_email(
    email_to: str,
    client_ip: str = "Unknown",
    user_agent: str = "Unknown"
) -> bool:
    """
    Send an immediate security notification email to `email_to` after a successful password reset.
    Alerts the user of the account modification without leaking any secrets or tokens.
    """
    settings = get_settings()
    if not settings.SECURITY_NOTIFICATION_ENABLED:
        return False

    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    from_email = settings.EMAILS_FROM_EMAIL or smtp_user or "noreply@plagiarism-ai.com"
    from_name = settings.EMAILS_FROM_NAME

    if not smtp_user or not smtp_password:
        logger.info(f"SMTP not configured. Skipping password-change security notification to {email_to}.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Security Alert: Your Password Was Changed — PlagiarismAI"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = email_to

        text_content = f"""
Hello,

This is a security notification to confirm that your PlagiarismAI account password was successfully reset.

All active sessions across all devices have been terminated.

If you made this change, no further action is required.
If you did NOT perform this action, please secure your account immediately and contact institutional support.

Best regards,
PlagiarismAI Security Team
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
    .title {{ font-size: 22px; font-weight: 700; color: #059669; margin: 0 0 4px 0; }}
    .body-text {{ font-size: 15px; line-height: 1.6; color: #334155; margin-bottom: 20px; }}
    .alert-box {{ background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px; margin: 20px 0; }}
    .footer {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h2 class="title">Security Notification</h2>
      <p style="font-size: 13px; color: #64748b; margin: 0;">Password Successfully Reset</p>
    </div>
    <div class="body-text">
      <p>Hello,</p>
      <p>Your <strong>PlagiarismAI</strong> account password was recently changed.</p>
      <div class="alert-box">
        <strong style="color: #15803d;">Active Sessions Terminated:</strong>
        <p style="margin: 4px 0 0 0; font-size: 13px; color: #166534;">
          As a security precaution, all existing active sessions across all your browsers and devices have been invalidated.
        </p>
      </div>
      <p>If you made this change, you can safely disregard this email.</p>
      <p style="color: #b91c1c; font-weight: 600;">
        If you did NOT change your password, someone else may have accessed your account. Please reset your password immediately or contact administrative support.
      </p>
    </div>
    <div class="footer">
      &copy; PlagiarismAI Security Operations. All rights reserved.
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

        logger.info(f"✅ Security notification email sent to {email_to}.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send security notification email to {email_to}: {e}")
        return False


def send_password_reset_otp_email(email_to: str, otp_code: str) -> bool:
    """
    Send a 6-digit one-time verification code when risk-based verification is triggered.
    Never logs the OTP code.
    """
    settings = get_settings()
    smtp_host = settings.SMTP_HOST
    smtp_port = settings.SMTP_PORT
    smtp_user = settings.SMTP_USER
    smtp_password = settings.SMTP_PASSWORD
    from_email = settings.EMAILS_FROM_EMAIL or smtp_user or "noreply@plagiarism-ai.com"
    from_name = settings.EMAILS_FROM_NAME

    if not smtp_user or not smtp_password:
        logger.info(f"SMTP not configured. Skipping OTP email dispatch to {email_to}.")
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "Your Password Reset Verification Code — PlagiarismAI"
        msg["From"] = f"{from_name} <{from_email}>"
        msg["To"] = email_to

        text_content = f"""
Hello,

Your verification code to complete your PlagiarismAI password reset is:

{otp_code}

This code is valid for {settings.PASSWORD_RESET_OTP_EXPIRY_MINUTES} minutes and can only be used once.

If you did not request this verification code, please ignore this email.

Best regards,
PlagiarismAI Security Team
"""

        html_content = f"""
<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f8fafc; margin: 0; padding: 20px; color: #0f172a; }}
    .container {{ max-width: 520px; margin: 0 auto; background: #ffffff; border-radius: 12px; border: 1px solid #e2e8f0; padding: 32px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1); }}
    .otp-code {{ font-size: 32px; font-weight: 800; letter-spacing: 6px; color: #4f46e5; background: #f8fafc; border: 1px dashed #cbd5e1; border-radius: 8px; padding: 16px; text-align: center; margin: 24px 0; }}
    .footer {{ text-align: center; font-size: 12px; color: #94a3b8; margin-top: 32px; border-top: 1px solid #f1f5f9; padding-top: 16px; }}
  </style>
</head>
<body>
  <div class="container">
    <div style="text-align: center; margin-bottom: 20px;">
      <h2 style="color: #4f46e5; margin: 0;">PlagiarismAI</h2>
      <p style="font-size: 13px; color: #64748b; margin: 4px 0 0 0;">Additional Security Verification</p>
    </div>
    <p style="font-size: 15px; color: #334155;">Hello,</p>
    <p style="font-size: 15px; color: #334155;">
      To verify your identity for resetting your account password, enter the following single-use verification code:
    </p>
    <div class="otp-code">{otp_code}</div>
    <p style="font-size: 13px; color: #64748b;">
      This code is valid for <strong>{settings.PASSWORD_RESET_OTP_EXPIRY_MINUTES} minutes</strong> and expires after single use.
    </p>
    <div class="footer">
      &copy; PlagiarismAI Security Operations. All rights reserved.
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

        logger.info(f"✅ OTP verification email sent to {email_to}.")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to send OTP email to {email_to}: {e}")
        return False


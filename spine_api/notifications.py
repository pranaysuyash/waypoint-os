"""
Follow-up Workflow Notifications

Handles operator reminders and traveler notifications for follow-up calls.
"""

import logging
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional, Dict, Any, List
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

logger = logging.getLogger(__name__)

# Configuration (in production, use environment variables)
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USERNAME = "notifications@travelagency.com"
SMTP_PASSWORD = None  # Set via environment variable


# =============================================================================
# OPERATOR EMAIL REMINDERS
# =============================================================================

def check_overdue_followups() -> List[Dict[str, Any]]:
    """
    Check for overdue follow-ups that need operator reminders.
    
    Returns list of trips with overdue follow-ups.
    """
    data_dir = Path(__file__).parent.parent / "data" / "trips"
    overdue = []
    now = datetime.now(timezone.utc)
    
    if not data_dir.exists():
        return overdue
    
    for trip_file in data_dir.glob("*.json"):
        try:
            with open(trip_file, "r") as f:
                trip = json.load(f)
            
            # Only check pending follow-ups
            if trip.get("follow_up_status", "pending") != "pending":
                continue
            
            due_date_str = trip.get("follow_up_due_date")
            if not due_date_str:
                continue
            
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue
            
            # Mark as overdue if past the due date
            if due_date < now:
                overdue.append({
                    "trip_id": trip.get("id"),
                    "traveler_name": trip.get("traveler_name", "Unknown"),
                    "agent_name": trip.get("agent_name", "Unassigned"),
                    "agent_email": trip.get("agent_email"),
                    "due_date": due_date_str,
                    "days_overdue": (now - due_date).days,
                })
        except (json.JSONDecodeError, IOError):
            continue
    
    return overdue


def format_operator_email_body(overdue_followups: List[Dict[str, Any]]) -> str:
    """Format the operator email body with overdue follow-ups."""
    body = """
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2 style="color: #e74c3c;">Overdue Follow-ups Reminder</h2>
    <p>You have <strong>{count}</strong> overdue follow-up{plural} that need your attention:</p>
    
    <table style="width: 100%; border-collapse: collapse; margin: 20px 0;">
      <thead>
        <tr style="background-color: #f5f5f5;">
          <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Trip</th>
          <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Traveler</th>
          <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Due Date</th>
          <th style="border: 1px solid #ddd; padding: 10px; text-align: left;">Overdue</th>
          <th style="border: 1px solid #ddd; padding: 10px; text-align: center;">Actions</th>
        </tr>
      </thead>
      <tbody>
""".format(
        count=len(overdue_followups),
        plural="s" if len(overdue_followups) != 1 else "",
    )
    
    for followup in overdue_followups:
        body += f"""
        <tr>
          <td style="border: 1px solid #ddd; padding: 10px;"><code>{followup['trip_id']}</code></td>
          <td style="border: 1px solid #ddd; padding: 10px;">{followup['traveler_name']}</td>
          <td style="border: 1px solid #ddd; padding: 10px;">{followup['due_date']}</td>
          <td style="border: 1px solid #ddd; padding: 10px;"><strong>{followup['days_overdue']} days</strong></td>
          <td style="border: 1px solid #ddd; padding: 10px; text-align: center;">
            <a href="#" style="color: #27ae60; text-decoration: none; margin: 0 5px;">✓ Complete</a>
            <a href="#" style="color: #f39c12; text-decoration: none; margin: 0 5px;">→ Snooze</a>
          </td>
        </tr>
"""
    
    body += """
      </tbody>
    </table>
    
    <p style="color: #7f8c8d; font-size: 12px; margin-top: 20px;">
      This is an automated reminder. Please update your follow-up status in the system.
    </p>
  </body>
</html>
"""
    return body


def send_operator_email(
    recipient_email: str,
    overdue_followups: List[Dict[str, Any]],
    subject: Optional[str] = None,
) -> bool:
    """
    Send operator email reminder for overdue follow-ups.
    
    In production, this would use AWS SES or SendGrid.
    For now, we log and return success (mock implementation).
    """
    if not recipient_email:
        logger.warning("No recipient email provided for operator notification")
        return False
    
    subject = subject or f"⏰ You have {len(overdue_followups)} overdue follow-up(s)"
    body = format_operator_email_body(overdue_followups)
    
    # Log the notification (mock implementation)
    logger.info(
        f"Operator notification: {subject}",
        extra={
            "recipient": recipient_email,
            "overdue_count": len(overdue_followups),
            "trips": [f['trip_id'] for f in overdue_followups],
        }
    )
    
    # In production, send via SMTP or email service:
    # try:
    #     msg = MIMEMultipart("alternative")
    #     msg["Subject"] = subject
    #     msg["From"] = SMTP_USERNAME
    #     msg["To"] = recipient_email
    #     msg.attach(MIMEText(body, "html"))
    #     
    #     with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
    #         server.starttls()
    #         server.login(SMTP_USERNAME, SMTP_PASSWORD)
    #         server.sendmail(SMTP_USERNAME, recipient_email, msg.as_string())
    #     return True
    # except Exception as e:
    #     logger.error(f"Failed to send operator email: {e}")
    #     return False
    
    return True


def send_daily_operator_reminders() -> int:
    """
    Check for overdue follow-ups and send daily reminders to operators.
    
    Returns: number of operators notified
    """
    overdue = check_overdue_followups()
    if not overdue:
        logger.info("No overdue follow-ups to remind about")
        return 0
    
    # Group by agent email
    by_agent: Dict[str, List[Dict[str, Any]]] = {}
    for followup in overdue:
        email = followup.get("agent_email")
        if email:
            if email not in by_agent:
                by_agent[email] = []
            by_agent[email].append(followup)
    
    # Send email to each agent
    notified = 0
    for email, followups in by_agent.items():
        if send_operator_email(email, followups):
            notified += 1
    
    return notified


# =============================================================================
# TRAVELER SMS/EMAIL NOTIFICATIONS
# =============================================================================

def check_upcoming_followups(hours_before: int = 24) -> List[Dict[str, Any]]:
    """
    Check for follow-ups due in the next N hours.
    
    Used for sending traveler notifications 24 hours before the call.
    """
    data_dir = Path(__file__).parent.parent / "data" / "trips"
    upcoming = []
    now = datetime.now(timezone.utc)
    cutoff = now + timedelta(hours=hours_before)
    
    if not data_dir.exists():
        return upcoming
    
    for trip_file in data_dir.glob("*.json"):
        try:
            with open(trip_file, "r") as f:
                trip = json.load(f)
            
            # Only check pending follow-ups
            if trip.get("follow_up_status", "pending") != "pending":
                continue
            
            due_date_str = trip.get("follow_up_due_date")
            if not due_date_str:
                continue
            
            try:
                due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
            except (ValueError, AttributeError):
                continue
            
            # Check if follow-up is coming up in the next 24 hours
            if now < due_date <= cutoff:
                upcoming.append({
                    "trip_id": trip.get("id"),
                    "traveler_name": trip.get("traveler_name", "Unknown"),
                    "traveler_phone": trip.get("traveler_phone"),
                    "traveler_email": trip.get("traveler_email"),
                    "agent_name": trip.get("agent_name", "Unassigned"),
                    "due_date": due_date_str,
                    "hours_until_due": (due_date - now).total_seconds() / 3600,
                })
        except (json.JSONDecodeError, IOError):
            continue
    
    return upcoming


def format_traveler_sms_body(traveler_name: str, agent_name: str, due_date_str: str) -> str:
    """Format SMS message for traveler."""
    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
    formatted_date = due_date.strftime("%b %d at %I:%M %p")
    return f"Hi {traveler_name}! {agent_name} will call you {formatted_date}. Looking forward to planning your trip! 🌍"


def format_traveler_email_body(traveler_name: str, agent_name: str, due_date_str: str) -> str:
    """Format email message for traveler."""
    due_date = datetime.fromisoformat(due_date_str.replace('Z', '+00:00'))
    formatted_date = due_date.strftime("%B %d at %I:%M %p")
    
    return f"""
<html>
  <body style="font-family: Arial, sans-serif; color: #333;">
    <h2>Hello {traveler_name},</h2>
    
    <p>We're excited to help you plan your trip! Your travel agent <strong>{agent_name}</strong> will be calling you on:</p>
    
    <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
      <p style="font-size: 18px; font-weight: bold; margin: 0;">📞 {formatted_date}</p>
    </div>
    
    <p>During this call, we'll discuss:</p>
    <ul>
      <li>Your travel dates and destinations</li>
      <li>Accommodation and activity preferences</li>
      <li>Budget and special requests</li>
      <li>The best options for your trip</li>
    </ul>
    
    <p>Please make sure you're available at the scheduled time. If you need to reschedule, reply to this email right away!</p>
    
    <p style="color: #7f8c8d;">
      Best regards,<br>
      The Travel Agency Team
    </p>
  </body>
</html>
"""


def send_traveler_notification(
    traveler_phone: Optional[str],
    traveler_email: Optional[str],
    traveler_name: str,
    agent_name: str,
    due_date_str: str,
) -> bool:
    """
    Send traveler notification (SMS or email) 24 hours before follow-up call.
    
    Prefers SMS if phone number available, falls back to email.
    """
    # Try SMS first
    if traveler_phone:
        message = format_traveler_sms_body(traveler_name, agent_name, due_date_str)
        logger.info(
            f"SMS notification to traveler",
            extra={
                "phone": traveler_phone,
                "traveler": traveler_name,
                "agent": agent_name,
                "message": message,
            }
        )
        # In production, send via Twilio or similar
        return True
    
    # Fall back to email
    if traveler_email:
        message = format_traveler_email_body(traveler_name, agent_name, due_date_str)
        logger.info(
            f"Email notification to traveler",
            extra={
                "email": traveler_email,
                "traveler": traveler_name,
                "agent": agent_name,
            }
        )
        # In production, send via SMTP or email service
        return True
    
    logger.warning(
        f"No phone or email for traveler {traveler_name}",
        extra={"trip_id": traveler_name},
    )
    return False


def send_traveler_upcoming_notifications() -> int:
    """
    Check for upcoming follow-ups and send traveler notifications.
    
    Returns: number of travelers notified
    """
    upcoming = check_upcoming_followups(hours_before=24)
    if not upcoming:
        logger.info("No upcoming follow-ups for traveler notifications")
        return 0
    
    notified = 0
    for followup in upcoming:
        if send_traveler_notification(
            followup.get("traveler_phone"),
            followup.get("traveler_email"),
            followup["traveler_name"],
            followup["agent_name"],
            followup["due_date"],
        ):
            notified += 1
    
    return notified


# =============================================================================
# SCHEDULED TASKS
# =============================================================================

def run_followup_notifications() -> Dict[str, int]:
    """
    Run all follow-up notification tasks.
    
    Should be called by a scheduler (e.g., APScheduler, Celery Beat).
    """
    return {
        "operator_reminders_sent": send_daily_operator_reminders(),
        "traveler_notifications_sent": send_traveler_upcoming_notifications(),
    }

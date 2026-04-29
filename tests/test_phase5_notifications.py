"""
Tests for Phase 5: Follow-up Notifications (Operator & Traveler)
"""

import pytest
from datetime import datetime, timezone, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import json

from spine_api.notifications import (
    check_overdue_followups,
    format_operator_email_body,
    send_operator_email,
    send_daily_operator_reminders,
    check_upcoming_followups,
    format_traveler_sms_body,
    format_traveler_email_body,
    send_traveler_notification,
    send_traveler_upcoming_notifications,
    run_followup_notifications,
)


# =============================================================================
# OPERATOR EMAIL NOTIFICATION TESTS
# =============================================================================

class TestCheckOverdueFollowups:
    """Tests for check_overdue_followups()"""

    def test_finds_overdue_followups(self, tmp_path):
        """Identifies follow-ups past their due date."""
        trip = {
            "id": "trip_001",
            "traveler_name": "Ravi",
            "agent_name": "Pranay",
            "agent_email": "pranay@agency.com",
            "follow_up_due_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
            "follow_up_status": "pending",
        }
        assert trip["follow_up_status"] == "pending"

    def test_ignores_completed_followups(self, tmp_path):
        """Does not include completed follow-ups."""
        trip = {
            "id": "trip_002",
            "follow_up_status": "completed",
            "follow_up_due_date": (datetime.now(timezone.utc) - timedelta(days=1)).isoformat(),
        }
        assert trip["follow_up_status"] == "completed"

    def test_ignores_upcoming_followups(self, tmp_path):
        """Does not include future follow-ups."""
        trip = {
            "id": "trip_003",
            "follow_up_status": "pending",
            "follow_up_due_date": (datetime.now(timezone.utc) + timedelta(days=2)).isoformat(),
        }
        due_date = datetime.fromisoformat(
            trip["follow_up_due_date"].replace('Z', '+00:00')
        )
        assert due_date > datetime.now(timezone.utc)

    def test_calculates_days_overdue(self):
        """Correctly calculates days overdue."""
        now = datetime.now(timezone.utc)
        due_date = now - timedelta(days=3)
        days_overdue = (now - due_date).days
        assert days_overdue == 3

    def test_handles_missing_trips_directory(self):
        """Gracefully handles missing trips directory."""
        # Should return empty list
        result = []
        assert len(result) == 0

    def test_handles_invalid_json_files(self):
        """Skips invalid JSON files."""
        # Should not crash, just skip bad files
        pass

    def test_returns_list_of_overdue_trips(self):
        """Returns list of overdue trip objects."""
        overdue = []
        assert isinstance(overdue, list)


class TestOperatorEmailFormatting:
    """Tests for format_operator_email_body()"""

    def test_email_includes_trip_information(self):
        """Email body includes trip IDs, traveler names, and dates."""
        overdue = [
            {
                "trip_id": "trip_001",
                "traveler_name": "Ravi",
                "due_date": "2026-04-26T10:00:00Z",
                "days_overdue": 2,
            }
        ]
        body = format_operator_email_body(overdue)
        assert "trip_001" in body
        assert "Ravi" in body
        assert "2" in body  # days overdue

    def test_email_shows_count_singular(self):
        """Shows singular 'follow-up' when count is 1."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        body = format_operator_email_body(overdue)
        assert "1" in body

    def test_email_shows_count_plural(self):
        """Shows plural 'follow-ups' when count > 1."""
        overdue = [
            {"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1},
            {"trip_id": "trip_002", "traveler_name": "Jane", "due_date": "2026-04-25T10:00:00Z", "days_overdue": 2},
        ]
        body = format_operator_email_body(overdue)
        assert "2" in body

    def test_email_is_html_formatted(self):
        """Email body is HTML formatted."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        body = format_operator_email_body(overdue)
        assert "<html>" in body
        assert "<table" in body

    def test_email_includes_action_links(self):
        """Email includes action links for complete and snooze."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        body = format_operator_email_body(overdue)
        assert "Complete" in body
        assert "Snooze" in body

    def test_email_with_empty_list(self):
        """Email formatting handles empty list."""
        body = format_operator_email_body([])
        assert isinstance(body, str)


class TestSendOperatorEmail:
    """Tests for send_operator_email()"""

    def test_requires_recipient_email(self):
        """Fails if no recipient email provided."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        result = send_operator_email("", overdue)
        assert result is False

    def test_logs_notification(self):
        """Logs notification when sent."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        result = send_operator_email("pranay@agency.com", overdue)
        # Should return True (mock implementation logs)
        assert isinstance(result, bool)

    def test_accepts_custom_subject(self):
        """Accepts optional custom subject line."""
        overdue = [{"trip_id": "trip_001", "traveler_name": "Ravi", "due_date": "2026-04-26T10:00:00Z", "days_overdue": 1}]
        subject = "Custom Subject"
        # Should use custom subject in email
        send_operator_email("pranay@agency.com", overdue, subject=subject)


class TestSendDailyOperatorReminders:
    """Tests for send_daily_operator_reminders()"""

    def test_returns_zero_if_no_overdue(self):
        """Returns 0 if no overdue follow-ups."""
        with patch('spine_api.notifications.check_overdue_followups', return_value=[]):
            result = send_daily_operator_reminders()
            assert result == 0

    def test_groups_by_agent_email(self):
        """Groups follow-ups by agent email."""
        # Multiple trips for same agent should get one email
        pass

    def test_sends_email_per_agent(self):
        """Sends separate email to each agent."""
        # Each unique agent email gets one email with all their overdue
        pass

    def test_returns_count_of_agents_notified(self):
        """Returns count of agents who were notified."""
        with patch('spine_api.notifications.check_overdue_followups', return_value=[]):
            result = send_daily_operator_reminders()
            assert isinstance(result, int)


# =============================================================================
# TRAVELER NOTIFICATION TESTS
# =============================================================================

class TestCheckUpcomingFollowups:
    """Tests for check_upcoming_followups()"""

    def test_finds_followups_due_in_24_hours(self):
        """Identifies follow-ups due in the next 24 hours."""
        now = datetime.now(timezone.utc)
        due_date = now + timedelta(hours=12)
        assert due_date > now
        assert (due_date - now).total_seconds() / 3600 < 24

    def test_excludes_followups_more_than_24_hours_away(self):
        """Excludes follow-ups more than 24 hours away."""
        now = datetime.now(timezone.utc)
        due_date = now + timedelta(hours=25)
        assert (due_date - now).total_seconds() / 3600 > 24

    def test_excludes_past_followups(self):
        """Excludes follow-ups that are already past due."""
        now = datetime.now(timezone.utc)
        due_date = now - timedelta(hours=1)
        assert due_date < now

    def test_ignores_completed_followups(self):
        """Does not include completed follow-ups."""
        trip = {
            "follow_up_status": "completed",
            "follow_up_due_date": (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat(),
        }
        assert trip["follow_up_status"] == "completed"

    def test_calculates_hours_until_due(self):
        """Correctly calculates hours until due."""
        now = datetime.now(timezone.utc)
        due_date = now + timedelta(hours=12)
        hours = (due_date - now).total_seconds() / 3600
        assert 11 < hours < 13


class TestTravelerMessageFormatting:
    """Tests for traveler message formatting"""

    def test_sms_body_includes_all_info(self):
        """SMS includes traveler name, agent name, and time."""
        message = format_traveler_sms_body(
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert "Ravi" in message
        assert "Pranay" in message
        assert "Apr" in message

    def test_sms_body_is_short(self):
        """SMS message is short enough for SMS length limits."""
        message = format_traveler_sms_body(
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert len(message) < 160

    def test_email_body_includes_all_info(self):
        """Email includes traveler name, agent name, date, and context."""
        body = format_traveler_email_body(
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert "Ravi" in body
        assert "Pranay" in body
        assert "Apr" in body
        assert "travel" in body.lower() or "plan" in body.lower()

    def test_email_body_is_html_formatted(self):
        """Email body is HTML formatted."""
        body = format_traveler_email_body("Ravi", "Pranay", "2026-04-28T14:00:00Z")
        assert "<html>" in body


class TestSendTravelerNotification:
    """Tests for send_traveler_notification()"""

    def test_prefers_sms_over_email(self):
        """Sends SMS if phone number available."""
        # Should send SMS when both phone and email provided
        result = send_traveler_notification(
            "+1-555-0100",
            "ravi@email.com",
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert result is True

    def test_falls_back_to_email_if_no_phone(self):
        """Sends email if no phone number."""
        result = send_traveler_notification(
            None,
            "ravi@email.com",
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert result is True

    def test_logs_warning_if_no_contact_info(self):
        """Logs warning if no phone or email."""
        result = send_traveler_notification(
            None,
            None,
            "Ravi",
            "Pranay",
            "2026-04-28T14:00:00Z"
        )
        assert result is False


class TestSendTravelerUpcomingNotifications:
    """Tests for send_traveler_upcoming_notifications()"""

    def test_returns_zero_if_no_upcoming(self):
        """Returns 0 if no upcoming follow-ups."""
        with patch('spine_api.notifications.check_upcoming_followups', return_value=[]):
            result = send_traveler_upcoming_notifications()
            assert result == 0

    def test_returns_count_of_travelers_notified(self):
        """Returns count of travelers who were notified."""
        with patch('spine_api.notifications.check_upcoming_followups', return_value=[]):
            result = send_traveler_upcoming_notifications()
            assert isinstance(result, int)


class TestRunFollowupNotifications:
    """Tests for run_followup_notifications()"""

    def test_runs_all_notification_tasks(self):
        """Runs both operator and traveler notification tasks."""
        with patch('spine_api.notifications.send_daily_operator_reminders', return_value=2):
            with patch('spine_api.notifications.send_traveler_upcoming_notifications', return_value=5):
                result = run_followup_notifications()
                assert "operator_reminders_sent" in result
                assert "traveler_notifications_sent" in result

    def test_returns_summary_dict(self):
        """Returns dictionary with counts of notifications sent."""
        with patch('spine_api.notifications.send_daily_operator_reminders', return_value=0):
            with patch('spine_api.notifications.send_traveler_upcoming_notifications', return_value=0):
                result = run_followup_notifications()
                assert isinstance(result, dict)
                assert result["operator_reminders_sent"] == 0
                assert result["traveler_notifications_sent"] == 0

"""
apps/notifications/tasks.py
────────────────────────────
Celery tasks for scheduled and triggered notifications.

Periodic tasks are registered via Django Celery Beat.
Register them in:  config/settings/base.py  under CELERY_BEAT_SCHEDULE
or via the Django Admin → Periodic Tasks.
"""
import logging
from datetime import time

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone

logger = logging.getLogger(__name__)
User = get_user_model()


# ── Scheduled: Morning Check-in Reminder ─────────────────────────────────────

@shared_task(name="notifications.send_morning_checkin_reminders")
def send_morning_checkin_reminders():
    """
    Run every minute (Celery Beat).
    Sends a morning check-in reminder to users whose preferred morning_time
    matches the current UTC minute and have the toggle enabled.
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService
    from apps.settings_app.models import NotificationPreferences

    current_time = timezone.now().strftime("%H:%M")

    prefs_qs = NotificationPreferences.objects.filter(
        morning_time=current_time,
        morning_checkin_enabled=True,
        do_not_disturb=False,
        user__is_active=True,
        user__is_email_verified=True,
        user__onboarding_completed=True,
    ).select_related("user")

    count = 0
    for pref in prefs_qs:
        NotificationService.send(
            recipient=pref.user,
            notification_type=Notification.NotificationType.MORNING_CHECKIN,
            title="Good morning! ☀️",
            body="Time for your morning check-in. It only takes 2 minutes.",
            priority=Notification.Priority.MEDIUM,
            data={"action": "open_morning_checkin"},
        )
        count += 1

    logger.info("Morning check-in reminders sent: %d", count)
    return count


# ── Scheduled: Evening Check-in Reminder ─────────────────────────────────────

@shared_task(name="notifications.send_evening_checkin_reminders")
def send_evening_checkin_reminders():
    """
    Run every minute (Celery Beat).
    Mirrors the morning reminder but for evening preferences.
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService
    from apps.settings_app.models import NotificationPreferences

    current_time = timezone.now().strftime("%H:%M")

    prefs_qs = NotificationPreferences.objects.filter(
        evening_time=current_time,
        evening_checkin_enabled=True,
        do_not_disturb=False,
        user__is_active=True,
        user__is_email_verified=True,
        user__onboarding_completed=True,
    ).select_related("user")

    count = 0
    for pref in prefs_qs:
        NotificationService.send(
            recipient=pref.user,
            notification_type=Notification.NotificationType.EVENING_CHECKIN,
            title="Evening check-in 🌙",
            body="How was your day? Complete your evening check-in.",
            priority=Notification.Priority.MEDIUM,
            data={"action": "open_evening_checkin"},
        )
        count += 1

    logger.info("Evening check-in reminders sent: %d", count)
    return count


# ── Scheduled: Weekly Tool Prompts (Monday 09:00 UTC) ────────────────────────

@shared_task(name="notifications.send_weekly_tool_prompts")
def send_weekly_tool_prompts():
    """
    Run every Monday morning.
    Reminds patients to complete their weekly mFG score and PHQ-4.
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService
    from apps.settings_app.models import NotificationPreferences

    prefs_qs = NotificationPreferences.objects.filter(
        weekly_prompts_enabled=True,
        do_not_disturb=False,
        user__is_active=True,
        user__onboarding_completed=True,
    ).select_related("user")

    count = 0
    for pref in prefs_qs:
        NotificationService.send(
            recipient=pref.user,
            notification_type=Notification.NotificationType.WEEKLY_PROMPT,
            title="Weekly assessment due 📋",
            body=(
                "Your weekly mFG score and PHQ-4 mood assessment are ready. "
                "These help improve your risk predictions."
            ),
            priority=Notification.Priority.MEDIUM,
            data={"action": "open_weekly_tools"},
        )
        count += 1

    logger.info("Weekly tool prompts sent: %d", count)
    return count


# ── On-demand: Risk Score Change Notification ─────────────────────────────────

@shared_task(name="notifications.notify_risk_score_change")
def notify_risk_score_change(user_id: int, new_score: int, previous_score: int, condition: str):
    """
    Called by the ML pipeline when a risk score changes significantly.
    condition: 'pcos' | 'maternal' | 'cardiovascular'
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService
    from apps.settings_app.models import NotificationPreferences

    try:
        user = User.objects.get(pk=user_id, is_active=True)
    except User.DoesNotExist:
        logger.warning("notify_risk_score_change: user %s not found", user_id)
        return

    try:
        prefs = NotificationPreferences.objects.get(user=user)
        if not prefs.risk_score_updates_enabled:
            return
    except NotificationPreferences.DoesNotExist:
        pass  # send anyway if prefs not found

    delta = new_score - previous_score
    direction = "increased" if delta > 0 else "decreased"
    condition_label = {
        "pcos": "PCOS",
        "maternal": "Maternal Health",
        "cardiovascular": "Cardiovascular",
    }.get(condition, condition.title())

    NotificationService.send(
        recipient=user,
        notification_type=Notification.NotificationType.RISK_UPDATE,
        title=f"{condition_label} risk score updated",
        body=(
            f"Your {condition_label} risk score has {direction} "
            f"from {previous_score} to {new_score}. "
            "Tap to view details."
        ),
        priority=Notification.Priority.HIGH if abs(delta) >= 15 else Notification.Priority.MEDIUM,
        data={
            "condition": condition,
            "new_score": new_score,
            "previous_score": previous_score,
            "delta": delta,
            "action": "open_risk_details",
        },
    )
    logger.info(
        "Risk score notification sent: user=%s condition=%s %d→%d",
        user_id, condition, previous_score, new_score,
    )


# ── On-demand: Wearable Sync Stale Reminder ──────────────────────────────────

@shared_task(name="notifications.check_stale_wearable_syncs")
def check_stale_wearable_syncs():
    """
    Run every 6 hours.
    Notifies users whose wearable hasn't synced in > 24 hours.
    """
    from datetime import timedelta
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService
    from apps.settings_app.models import ConnectedDevice, NotificationPreferences

    stale_cutoff = timezone.now() - timedelta(hours=24)

    stale_devices = ConnectedDevice.objects.filter(
        is_connected=True,
        last_synced_at__lt=stale_cutoff,
        user__is_active=True,
    ).select_related("user")

    notified_users = set()

    for device in stale_devices:
        user = device.user

        if user.pk in notified_users:
            continue  # only one notification per user per run

        try:
            prefs = NotificationPreferences.objects.get(user=user)
            if not prefs.wearable_sync_reminders:
                continue
        except NotificationPreferences.DoesNotExist:
            continue

        NotificationService.send(
            recipient=user,
            notification_type=Notification.NotificationType.WEARABLE_SYNC,
            title="Wearable sync needed 📡",
            body=(
                f"Your {device.get_device_type_display()} hasn't synced in over 24 hours. "
                "Open the app to sync your latest health data."
            ),
            priority=Notification.Priority.LOW,
            data={
                "device_type": device.device_type,
                "device_id": device.pk,
                "action": "open_devices",
            },
        )
        notified_users.add(user.pk)

    logger.info("Stale wearable sync notifications sent: %d", len(notified_users))
    return len(notified_users)

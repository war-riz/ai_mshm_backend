"""
apps/centers/signals.py
────────────────────────
Handles escalation notifications to Health Care Centers and Federal Health Centers
when a patient's risk prediction reaches SEVERE or VERY SEVERE.

HOW IT WORKS:
    1. ML prediction pipeline calls: notify_center_of_critical_risk(patient, result)
    2. This finds the clinician linked to the patient (if any)
    3. Routes SEVERE → HCC, VERY_SEVERE → both HCC and FHC
    4. Sends in-app notifications to the center admin users
    5. Also sends in-app notification to the linked clinician

This is a standalone function (not a Django signal) because it's called
explicitly from the prediction pipeline. It lives here for co-location.
"""
import logging
from django.contrib.auth import get_user_model

from .models import RiskSeverity, ClinicianProfile

logger = logging.getLogger(__name__)
User = get_user_model()


def notify_center_of_critical_risk(
    patient: User,
    condition: str,
    severity: str,
    score: int,
    previous_score: int = None,
) -> None:
    """
    Called by the ML prediction pipeline after computing a new risk score.

    Args:
        patient:        The User (role=patient) whose score changed.
        condition:      'pcos' | 'maternal' | 'cardiovascular'
        severity:       One of RiskSeverity values
        score:          New risk score (0–100)
        previous_score: Prior score (optional)
    """
    from apps.notifications.models import Notification
    from apps.notifications.services import NotificationService

    if severity not in (RiskSeverity.SEVERE, RiskSeverity.VERY_SEVERE):
        return  # Only escalate on severe or very severe

    condition_label = {
        "pcos": "PCOS",
        "maternal": "Maternal Health",
        "cardiovascular": "Cardiovascular",
    }.get(condition, condition.title())

    severity_label = dict(RiskSeverity.choices).get(severity, severity)

    # ── Find linked clinician (if any) ────────────────────────────────────────
    clinician_profile = None
    try:
        # In future: patient will have an explicit clinician FK
        # For now: find any verified clinician in the same HCC/FHC who is marked
        # as the patient's care provider — stubbed as a direct lookup by patient relation
        clinician_profile = ClinicianProfile.objects.filter(
            user__is_active=True,
            is_verified=True,
        ).first()  # TODO: replace with actual patient→clinician relationship
    except Exception:
        pass

    notification_data = {
        "patient_email": patient.email,
        "patient_name": patient.full_name,
        "condition": condition,
        "severity": severity,
        "score": score,
        "previous_score": previous_score,
        "action": "open_patient_risk_report",
    }

    # ── Notify linked clinician ───────────────────────────────────────────────
    if clinician_profile:
        NotificationService.send(
            recipient=clinician_profile.user,
            notification_type=Notification.NotificationType.RISK_UPDATE,
            title=f"⚠️ Patient alert: {severity_label} {condition_label} risk",
            body=(
                f"{patient.full_name}'s {condition_label} risk score is now "
                f"{severity_label} ({score}/100). Immediate review recommended."
            ),
            priority=Notification.Priority.HIGH,
            data=notification_data,
        )
        logger.info(
            "Escalation sent to clinician %s for patient %s: %s %s",
            clinician_profile.user.email, patient.email, condition, severity,
        )

    # ── Notify HCC admin (SEVERE and VERY SEVERE) ─────────────────────────────
    if clinician_profile and clinician_profile.hcc:
        hcc = clinician_profile.hcc
        if hcc.notify_on_severe or (severity == RiskSeverity.VERY_SEVERE and hcc.notify_on_very_severe):
            if hcc.admin_user:
                NotificationService.send(
                    recipient=hcc.admin_user,
                    notification_type=Notification.NotificationType.RISK_UPDATE,
                    title=f"🏥 Center alert: {severity_label} case",
                    body=(
                        f"A patient at {hcc.name} has reached {severity_label} "
                        f"{condition_label} risk ({score}/100)."
                    ),
                    priority=Notification.Priority.HIGH,
                    data={**notification_data, "center": hcc.name},
                )
                logger.info("Escalation sent to HCC admin %s", hcc.admin_user.email)

    # ── Notify FHC admin (VERY SEVERE only — critical escalation) ────────────
    if severity == RiskSeverity.VERY_SEVERE:
        if clinician_profile and clinician_profile.fhc:
            fhc = clinician_profile.fhc
            if fhc.notify_on_very_severe and fhc.admin_user:
                NotificationService.send(
                    recipient=fhc.admin_user,
                    notification_type=Notification.NotificationType.RISK_UPDATE,
                    title=f"🚨 Critical: Very Severe {condition_label} case",
                    body=(
                        f"A patient under {fhc.name} jurisdiction has reached "
                        f"VERY SEVERE {condition_label} risk ({score}/100). "
                        "Immediate federal-level intervention may be required."
                    ),
                    priority=Notification.Priority.HIGH,
                    data={**notification_data, "center": fhc.name, "critical": True},
                )
                logger.info("Critical escalation sent to FHC admin %s", fhc.admin_user.email)

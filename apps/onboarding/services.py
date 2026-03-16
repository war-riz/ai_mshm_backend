"""
apps/onboarding/services.py
────────────────────────────
Business logic helpers for the onboarding flow.
Views call these helpers to keep view code thin.
"""
import logging

from django.contrib.auth import get_user_model
from .models import OnboardingProfile

logger = logging.getLogger(__name__)
User = get_user_model()


class OnboardingService:

    @staticmethod
    def get_or_create_profile(user) -> OnboardingProfile:
        profile, created = OnboardingProfile.objects.get_or_create(user=user)
        if created:
            logger.debug("Created onboarding profile for %s", user.email)
        return profile

    @staticmethod
    def advance_step(user, completed_step: int) -> None:
        """
        Advance user.onboarding_step if completed_step is further than current.
        Never goes backwards (re-submitting step 2 after step 4 shouldn't regress).
        """
        if completed_step > user.onboarding_step:
            user.onboarding_step = completed_step
            user.save(update_fields=["onboarding_step"])

    @staticmethod
    def completion_percentage(user) -> int:
        """
        Returns 0–100 based on how many of the 6 steps are complete.
        Used by dashboard progress indicators.
        """
        TOTAL_STEPS = 6
        step = min(user.onboarding_step, TOTAL_STEPS)
        return round((step / TOTAL_STEPS) * 100)

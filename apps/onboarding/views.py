"""
apps/onboarding/views.py
─────────────────────────
Step-based onboarding endpoints — one view per step so Swagger
shows the exact request body schema for each step.

Flow:
    PATCH /api/v1/onboarding/step/1/       →  Personal Info
    PATCH /api/v1/onboarding/step/2/       →  Physical Measurements
    PATCH /api/v1/onboarding/step/3/       →  Skin Changes
    PATCH /api/v1/onboarding/step/4/       →  Menstrual History
    PATCH /api/v1/onboarding/step/5/       →  Wearable Setup
    POST  /api/v1/onboarding/step/6/rppg/  →  rPPG Baseline
    POST  /api/v1/onboarding/complete/     →  Mark complete → dashboard
    GET   /api/v1/onboarding/profile/      →  Full onboarding data
"""
from django.utils import timezone
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from drf_spectacular.utils import extend_schema

from core.responses import success_response, error_response
from .serializers import (
    Step1PersonalInfoSerializer,
    Step2PhysicalMeasurementsSerializer,
    Step3SkinChangesSerializer,
    Step4MenstrualHistorySerializer,
    Step5WearableSerializer,
    Step6RppgSerializer,
    OnboardingProfileSerializer,
)
from .services import OnboardingService


# ── Step 1: Personal Info ─────────────────────────────────────────────────────

class OnboardingStep1View(APIView):
    """
    PATCH /api/v1/onboarding/step/1/
    Fields: full_name, age, ethnicity
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step1PersonalInfoSerializer,
        responses={200: Step1PersonalInfoSerializer},
        summary="Step 1 – Personal Info",
        description=(
            "Submit personal info.\n\n"
            "- `full_name` — string\n"
            "- `age` — integer (10–120)\n"
            "- `ethnicity` — `white` | `black` | `hispanic` | `asian` | "
            "`south_asian` | `middle_eastern` | `mixed` | `prefer_not`"
        ),
    )
    def patch(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        serializer = Step1PersonalInfoSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        OnboardingService.advance_step(request.user, 1)
        return success_response(
            data=serializer.data,
            message="Step 1 (Personal Info) saved successfully.",
        )


# ── Step 2: Physical Measurements ─────────────────────────────────────────────

class OnboardingStep2View(APIView):
    """
    PATCH /api/v1/onboarding/step/2/
    Fields: height_cm, weight_kg (BMI auto-computed)
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step2PhysicalMeasurementsSerializer,
        responses={200: Step2PhysicalMeasurementsSerializer},
        summary="Step 2 – Physical Measurements",
        description=(
            "Submit physical measurements. BMI is computed automatically.\n\n"
            "- `height_cm` — float (50–300)\n"
            "- `weight_kg` — float (20–500)"
        ),
    )
    def patch(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        serializer = Step2PhysicalMeasurementsSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        OnboardingService.advance_step(request.user, 2)
        return success_response(
            data=serializer.data,
            message="Step 2 (Physical Measurements) saved successfully.",
        )


# ── Step 3: Skin Changes ──────────────────────────────────────────────────────

class OnboardingStep3View(APIView):
    """
    PATCH /api/v1/onboarding/step/3/
    Fields: has_skin_changes
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step3SkinChangesSerializer,
        responses={200: Step3SkinChangesSerializer},
        summary="Step 3 – Skin Changes",
        description=(
            "Submit skin change info (Acanthosis Nigricans screening).\n\n"
            "- `has_skin_changes` — boolean (`true` / `false`)"
        ),
    )
    def patch(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        serializer = Step3SkinChangesSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        OnboardingService.advance_step(request.user, 3)
        return success_response(
            data=serializer.data,
            message="Step 3 (Skin Changes) saved successfully.",
        )


# ── Step 4: Menstrual History ─────────────────────────────────────────────────

class OnboardingStep4View(APIView):
    """
    PATCH /api/v1/onboarding/step/4/
    Fields: cycle_length_days, periods_per_year, cycle_regularity
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step4MenstrualHistorySerializer,
        responses={200: Step4MenstrualHistorySerializer},
        summary="Step 4 – Menstrual History",
        description=(
            "Submit menstrual history.\n\n"
            "- `cycle_length_days` — integer (1–90)\n"
            "- `periods_per_year` — integer (0–14)\n"
            "- `cycle_regularity` — `regular` | `irregular`"
        ),
    )
    def patch(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        serializer = Step4MenstrualHistorySerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        OnboardingService.advance_step(request.user, 4)
        return success_response(
            data=serializer.data,
            message="Step 4 (Menstrual History) saved successfully.",
        )


# ── Step 5: Wearable Setup ────────────────────────────────────────────────────

class OnboardingStep5View(APIView):
    """
    PATCH /api/v1/onboarding/step/5/
    Fields: selected_wearable
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step5WearableSerializer,
        responses={200: Step5WearableSerializer},
        summary="Step 5 – Wearable Setup",
        description=(
            "Submit wearable device selection.\n\n"
            "- `selected_wearable` — `apple_watch` | `fitbit` | `garmin` | `oura_ring` | `none`"
        ),
    )
    def patch(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        serializer = Step5WearableSerializer(profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        OnboardingService.advance_step(request.user, 5)
        return success_response(
            data=serializer.data,
            message="Step 5 (Wearable Setup) saved successfully.",
        )


# ── Step 6: rPPG Baseline ─────────────────────────────────────────────────────

class OnboardingRppgView(APIView):
    """
    POST /api/v1/onboarding/step/6/rppg/
    Marks the rPPG baseline scan as captured.
    Actual video/signal upload hits a separate media pipeline endpoint.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        request=Step6RppgSerializer,
        summary="Step 6 – rPPG Baseline",
        description=(
            "Mark the rPPG baseline scan as captured on the device.\n\n"
            "- `baseline_captured` — must be `true`\n\n"
            "The actual signal data is handled by the media pipeline separately."
        ),
    )
    def post(self, request):
        serializer = Step6RppgSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data["baseline_captured"]:
            return error_response("baseline_captured must be true to record the scan.")

        profile = OnboardingService.get_or_create_profile(request.user)
        profile.rppg_baseline_captured = True
        profile.rppg_captured_at = timezone.now()
        profile.save(update_fields=["rppg_baseline_captured", "rppg_captured_at"])

        OnboardingService.advance_step(request.user, 6)

        # Return the captured flags so frontend can confirm the scan was recorded
        return success_response(
            message="rPPG baseline recorded successfully.",
            data={
                "rppg_baseline_captured": profile.rppg_baseline_captured,
                "rppg_captured_at": profile.rppg_captured_at,
            }
        )


# ── Complete Onboarding ───────────────────────────────────────────────────────

class OnboardingCompleteView(APIView):
    """
    POST /api/v1/onboarding/complete/
    Call after all steps are done (step 5 minimum, step 6 optional).
    Sets onboarding_completed = True on the user.
    Frontend redirects to /dashboard on success.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        summary="Mark onboarding as complete",
        description=(
            "Finalises onboarding. Sets `onboarding_completed = true` on the user.\n\n"
            "Response includes a `redirect` hint for the frontend to navigate to the dashboard."
        ),
    )
    def post(self, request):
        user = request.user
        user.onboarding_completed = True
        user.onboarding_step = 6
        user.save(update_fields=["onboarding_completed", "onboarding_step"])

        # Return full profile so frontend has everything fresh for the dashboard
        profile = OnboardingService.get_or_create_profile(user)

        return success_response(
            message="Onboarding complete. Welcome to AI-MSHM!",
            data={
                "redirect": "/dashboard",
                "onboarding_completed": user.onboarding_completed,
                "onboarding_step": user.onboarding_step,
                "profile": OnboardingProfileSerializer(profile).data,
            }
        )


# ── Full Profile (read-only) ──────────────────────────────────────────────────

class OnboardingProfileView(APIView):
    """
    GET /api/v1/onboarding/profile/
    Returns the full onboarding profile for the authenticated user.
    Useful for pre-filling forms or showing a summary screen.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Onboarding"],
        summary="Get current user's full onboarding profile",
        responses={200: OnboardingProfileSerializer},
        description="Returns all saved onboarding data. Creates an empty profile if none exists yet.",
    )
    def get(self, request):
        profile = OnboardingService.get_or_create_profile(request.user)
        return success_response(
            data=OnboardingProfileSerializer(profile).data
        )
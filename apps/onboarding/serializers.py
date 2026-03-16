"""
apps/onboarding/serializers.py
───────────────────────────────
Each step has its own serializer. This keeps validation focused
and lets the frontend submit steps independently.
"""
from rest_framework import serializers
from .models import OnboardingProfile


class Step1PersonalInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardingProfile
        fields = ["full_name", "age", "ethnicity"]

    def validate_age(self, value):
        if value is not None and not (10 <= value <= 120):
            raise serializers.ValidationError("Age must be between 10 and 120.")
        return value


class Step2PhysicalMeasurementsSerializer(serializers.ModelSerializer):
    bmi = serializers.FloatField(read_only=True)

    class Meta:
        model  = OnboardingProfile
        fields = ["height_cm", "weight_kg", "bmi"]

    def validate_height_cm(self, value):
        if value is not None and not (50 <= value <= 300):
            raise serializers.ValidationError("Height must be between 50 and 300 cm.")
        return value

    def validate_weight_kg(self, value):
        if value is not None and not (20 <= value <= 500):
            raise serializers.ValidationError("Weight must be between 20 and 500 kg.")
        return value


class Step3SkinChangesSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardingProfile
        fields = ["has_skin_changes"]

    def validate_has_skin_changes(self, value):
        if value is None:
            raise serializers.ValidationError("Please select Yes or No.")
        return value


class Step4MenstrualHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardingProfile
        fields = ["cycle_length_days", "periods_per_year", "cycle_regularity"]

    def validate_cycle_length_days(self, value):
        if value is not None and not (1 <= value <= 90):
            raise serializers.ValidationError("Cycle length must be between 1 and 90 days.")
        return value

    def validate_periods_per_year(self, value):
        if value is not None and not (0 <= value <= 14):
            raise serializers.ValidationError("Periods per year must be between 0 and 14.")
        return value


class Step5WearableSerializer(serializers.ModelSerializer):
    class Meta:
        model  = OnboardingProfile
        fields = ["selected_wearable"]


class Step6RppgSerializer(serializers.Serializer):
    """
    Placeholder. The real rPPG pipeline will receive a video
    blob; for now we just flag the baseline as captured.
    """
    baseline_captured = serializers.BooleanField()


class OnboardingProfileSerializer(serializers.ModelSerializer):
    """Full read serializer — returned after completion."""
    bmi = serializers.FloatField(read_only=True)

    class Meta:
        model  = OnboardingProfile
        fields = [
            "full_name", "age", "ethnicity",
            "height_cm", "weight_kg", "bmi",
            "has_skin_changes",
            "cycle_length_days", "periods_per_year", "cycle_regularity",
            "selected_wearable",
            "rppg_baseline_captured", "rppg_captured_at",
            "created_at", "updated_at",
        ]
        read_only_fields = ["bmi", "rppg_captured_at", "created_at", "updated_at"]

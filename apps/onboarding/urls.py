"""
apps/onboarding/urls.py
Base prefix: /api/v1/onboarding/
"""
from django.urls import path
from .views import (
    OnboardingStep1View,
    OnboardingStep2View,
    OnboardingStep3View,
    OnboardingStep4View,
    OnboardingStep5View,
    OnboardingRppgView,
    OnboardingCompleteView,
    OnboardingProfileView,
)

app_name = "onboarding"

urlpatterns = [
    path("profile/",     OnboardingProfileView.as_view(), name="profile"),
    path("step/1/",      OnboardingStep1View.as_view(),   name="step-1"),
    path("step/2/",      OnboardingStep2View.as_view(),   name="step-2"),
    path("step/3/",      OnboardingStep3View.as_view(),   name="step-3"),
    path("step/4/",      OnboardingStep4View.as_view(),   name="step-4"),
    path("step/5/",      OnboardingStep5View.as_view(),   name="step-5"),
    path("step/6/rppg/", OnboardingRppgView.as_view(),    name="step-6-rppg"),
    path("complete/",    OnboardingCompleteView.as_view(), name="complete"),
]
"""
apps/centers/urls.py
Base prefix: /api/v1/centers/
"""
from django.urls import path
from .views import (
    HCCListPublicView,
    FHCListPublicView,
    ClinicianProfileView,
    HCCAdminListView,
    HCCAdminDetailView,
    FHCAdminListView,
    FHCAdminDetailView,
)

app_name = "centers"

urlpatterns = [
    # ── Public dropdowns (no auth required) ──────────────────────────────────
    path("hcc/",                    HCCListPublicView.as_view(),    name="hcc-list-public"),
    path("fhc/",                    FHCListPublicView.as_view(),    name="fhc-list-public"),

    # ── Clinician: own profile ────────────────────────────────────────────────
    path("clinician/profile/",      ClinicianProfileView.as_view(), name="clinician-profile"),

    # ── Platform admin: HCC management ───────────────────────────────────────
    path("admin/hcc/",              HCCAdminListView.as_view(),     name="admin-hcc-list"),
    path("admin/hcc/<int:pk>/",     HCCAdminDetailView.as_view(),   name="admin-hcc-detail"),

    # ── Platform admin: FHC management ───────────────────────────────────────
    path("admin/fhc/",              FHCAdminListView.as_view(),     name="admin-fhc-list"),
    path("admin/fhc/<int:pk>/",     FHCAdminDetailView.as_view(),   name="admin-fhc-detail"),
]

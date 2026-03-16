"""
apps/centers/models.py
───────────────────────
Health Care Center (HCC) and Federal Health Center (FHC) models.
A Clinician links to exactly one of these via ClinicianProfile.

Severity enum used by the ML prediction layer is also defined here
so it can be imported from one canonical place.
"""
import uuid 
from django.db import models
from django.conf import settings


# ── Shared severity enum (used by prediction output) ─────────────────────────

class RiskSeverity(models.TextChoices):
    """
    Standard severity scale for all AI-MSHM prediction outputs.
    Used in: PCOS prediction, Maternal Health, Cardiovascular risk.
    """
    MILD        = "mild",        "Mild"
    MODERATE    = "moderate",    "Moderate"
    SEVERE      = "severe",      "Severe"
    VERY_SEVERE = "very_severe", "Very Severe"


# ── Health Care Center ────────────────────────────────────────────────────────

class HealthCareCenter(models.Model):
    """
    A local/private health care center.
    Clinicians belong here.
    HCC can VIEW patient risk scores when the patient consents.
    HCC gets notified on SEVERE results.
    """

    class CenterStatus(models.TextChoices):
        ACTIVE   = "active",   "Active"
        INACTIVE = "inactive", "Inactive"
        PENDING  = "pending",  "Pending Verification"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    name         = models.CharField(max_length=255, unique=True)
    code         = models.CharField(max_length=20, unique=True, help_text="Short identifier e.g. LGH-001")
    address      = models.TextField(blank=True)
    state        = models.CharField(max_length=100, blank=True)
    lga          = models.CharField(max_length=100, blank=True, verbose_name="LGA")
    phone        = models.CharField(max_length=20, blank=True)
    email        = models.EmailField(blank=True)
    website      = models.URLField(blank=True)
    status       = models.CharField(max_length=15, choices=CenterStatus.choices, default=CenterStatus.ACTIVE)

    # Notification settings
    notify_on_severe      = models.BooleanField(default=True)
    notify_on_very_severe = models.BooleanField(default=True)

    # Admin user for this center
    admin_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="managed_hcc",
        limit_choices_to={"role": "hcc_admin"},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Health Care Center"
        verbose_name_plural = "Health Care Centers"
        ordering            = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ── Federal Health Center ─────────────────────────────────────────────────────

class FederalHealthCenter(models.Model):
    """
    A government / federal health facility.
    Clinicians can belong here too.
    FHC gets notified on VERY SEVERE results (critical escalation).
    FHC has broader oversight — can see aggregated anonymised stats.
    """

    class CenterStatus(models.TextChoices):
        ACTIVE   = "active",   "Active"
        INACTIVE = "inactive", "Inactive"
        PENDING  = "pending",  "Pending Verification"

    id           = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    name         = models.CharField(max_length=255, unique=True)
    code         = models.CharField(max_length=20, unique=True, help_text="Short identifier e.g. FHC-ABJ-001")
    address      = models.TextField(blank=True)
    state        = models.CharField(max_length=100, blank=True)
    zone         = models.CharField(max_length=100, blank=True, help_text="Geopolitical zone")
    phone        = models.CharField(max_length=20, blank=True)
    email        = models.EmailField(blank=True)
    status       = models.CharField(max_length=15, choices=CenterStatus.choices, default=CenterStatus.ACTIVE)

    # FHC always gets notified on very severe — this is a hard rule
    notify_on_very_severe = models.BooleanField(default=True, editable=False)

    # Admin user for this center
    admin_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="managed_fhc",
        limit_choices_to={"role": "fhc_admin"},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name        = "Federal Health Center"
        verbose_name_plural = "Federal Health Centers"
        ordering            = ["state", "name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ── Clinician Profile ─────────────────────────────────────────────────────────

class ClinicianProfile(models.Model):
    """
    Extended profile for users with role='clinician'.
    Links the clinician to exactly one HCC or FHC.
    """

    class CenterType(models.TextChoices):
        HCC = "hcc", "Health Care Center"
        FHC = "fhc", "Federal Health Center"

    class Specialization(models.TextChoices):
        GENERAL_PRACTICE  = "general_practice",  "General Practice"
        OBSTETRICS_GYNAE  = "obstetrics_gynae",   "Obstetrics & Gynaecology"
        ENDOCRINOLOGY     = "endocrinology",      "Endocrinology"
        CARDIOLOGY        = "cardiology",         "Cardiology"
        INTERNAL_MEDICINE = "internal_medicine",  "Internal Medicine"
        REPRODUCTIVE_HEALTH = "reproductive_health", "Reproductive Health"
        MIDWIFERY         = "midwifery",          "Midwifery"
        NURSING           = "nursing",            "Nursing"
        OTHER             = "other",              "Other"

    id               = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user             = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="clinician_profile")
    specialization   = models.CharField(max_length=30, choices=Specialization.choices, default=Specialization.GENERAL_PRACTICE)
    license_number   = models.CharField(max_length=50, blank=True, help_text="MDCN or relevant body license number")
    years_of_experience = models.PositiveSmallIntegerField(default=0)
    bio              = models.TextField(blank=True)

    # Center affiliation — exactly one of these will be non-null
    center_type      = models.CharField(max_length=5, choices=CenterType.choices)
    hcc              = models.ForeignKey(
        HealthCareCenter, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="clinicians",
    )
    fhc              = models.ForeignKey(
        FederalHealthCenter, on_delete=models.SET_NULL,
        null=True, blank=True, related_name="clinicians",
    )

    # Verification
    is_verified      = models.BooleanField(default=False)
    verified_at      = models.DateTimeField(null=True, blank=True)

    # Profile photo (Cloudinary)
    profile_photo    = models.ImageField(upload_to="clinicians/", null=True, blank=True)

    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Clinician Profile"

    def __str__(self):
        return f"Dr. {self.user.full_name} — {self.get_specialization_display()}"

    @property
    def center_name(self) -> str:
        """Human-readable name of the affiliated center."""
        if self.center_type == self.CenterType.HCC and self.hcc:
            return self.hcc.name
        if self.center_type == self.CenterType.FHC and self.fhc:
            return self.fhc.name
        return "Unaffiliated"

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.center_type == self.CenterType.HCC and not self.hcc_id:
            raise ValidationError("HCC clinicians must be linked to a Health Care Center.")
        if self.center_type == self.CenterType.FHC and not self.fhc_id:
            raise ValidationError("FHC clinicians must be linked to a Federal Health Center.")
        if self.hcc_id and self.fhc_id:
            raise ValidationError("A clinician cannot be linked to both HCC and FHC.")

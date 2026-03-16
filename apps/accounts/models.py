"""
apps/accounts/models.py
────────────────────────
Custom User model + EmailVerificationToken + PasswordResetToken
All stored in MongoDB via Djongo.
"""
import uuid
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models
from django.utils import timezone
from core.storage import AvatarStorage


class UserManager(BaseUserManager):
    def create_user(self, email: str, password: str = None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email: str, password: str, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", User.Role.ADMIN)
        extra_fields.setdefault("is_email_verified", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """
    Central user model shared by Patient, Clinician, and Admin roles.
    Role-specific profile data lives in separate profile documents.
    """

    class Role(models.TextChoices):
        PATIENT   = "patient",    "Patient"
        CLINICIAN = "clinician",  "Clinician"
        HCC_ADMIN = "hcc_admin",  "Health Care Center Admin"
        FHC_ADMIN = "fhc_admin",  "Federal Health Center Admin"
        ADMIN     = "admin",      "Platform Admin"

    # ── Core identity ─────────────────────────────────────────────────────────
    id                = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    email             = models.EmailField(unique=True, db_index=True)
    full_name         = models.CharField(max_length=255)
    role              = models.CharField(max_length=20, choices=Role.choices, default=Role.PATIENT)

    # ── Auth state ────────────────────────────────────────────────────────────
    is_active         = models.BooleanField(default=True)
    is_staff          = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)

    # ── Onboarding progress ───────────────────────────────────────────────────
    onboarding_completed = models.BooleanField(default=False)
    onboarding_step      = models.PositiveSmallIntegerField(default=0)  # 0–5

    # ── Avatar (Cloudinary) ───────────────────────────────────────────────────
    avatar = models.ImageField(storage=AvatarStorage(), null=True, blank=True)

    # ── Timestamps ────────────────────────────────────────────────────────────
    date_joined = models.DateTimeField(default=timezone.now)
    last_login  = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["full_name"]

    class Meta:
        ordering = ["-date_joined"]
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def display_name(self):
        return self.full_name or self.email.split("@")[0]

    @property
    def is_patient(self):
        return self.role == self.Role.PATIENT

    @property
    def is_clinician(self):
        return self.role == self.Role.CLINICIAN

    @property
    def is_hcc_admin(self):
        return self.role == self.Role.HCC_ADMIN

    @property
    def is_fhc_admin(self):
        return self.role == self.Role.FHC_ADMIN

    @property
    def is_center_admin(self):
        return self.role in (self.Role.HCC_ADMIN, self.Role.FHC_ADMIN)


# ── Email Verification ────────────────────────────────────────────────────────

class EmailVerificationToken(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user       = models.OneToOneField(User, on_delete=models.CASCADE, related_name="email_token")
    token_hash = models.CharField(max_length=64, db_index=True)   # SHA-256 of raw token
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Email Verification Token"

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"EmailToken({self.user.email})"


# ── Password Reset ────────────────────────────────────────────────────────────

class PasswordResetToken(models.Model):
    id         = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False) 
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="password_tokens")
    token_hash = models.CharField(max_length=64, db_index=True)
    expires_at = models.DateTimeField()
    is_used    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Password Reset Token"
        ordering = ["-created_at"]

    def is_expired(self) -> bool:
        return timezone.now() > self.expires_at

    def __str__(self):
        return f"PasswordReset({self.user.email})"

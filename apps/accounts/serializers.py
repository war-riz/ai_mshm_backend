"""
apps/accounts/serializers.py
─────────────────────────────
Serializers for registration, login, email verification, and password reset.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from core.validators import validate_image

User = get_user_model()


# ── JWT customisation ─────────────────────────────────────────────────────────

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds user metadata into the JWT payload and login response."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"]  = user.role
        token["name"]  = user.full_name
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user

        # Guard: block unverified users from logging in
        if not user.is_email_verified:
            raise serializers.ValidationError(
                {
                    "email": "Please verify your email address before logging in.",
                    "code": "email_not_verified",
                }
            )

        data["user"] = UserProfileSerializer(user).data
        return data


# ── Registration ──────────────────────────────────────────────────────────────

class RegisterSerializer(serializers.ModelSerializer):
    password         = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model  = User
        fields = ["full_name", "email", "password", "confirm_password", "role"]
        extra_kwargs = {
            "role": {"required": False},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs.pop("confirm_password"):
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs

    def validate_role(self, value):
        # Prevent self-registration as platform admin
        if value == User.Role.ADMIN:
            raise serializers.ValidationError("Cannot self-register with admin role.")
        return value

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


# ── User profile (read-only, embeds in responses) ────────────────────────────

class UserProfileSerializer(serializers.ModelSerializer):
    avatar_url    = serializers.SerializerMethodField()
    center_info   = serializers.SerializerMethodField()
    id            = serializers.CharField(read_only=True)

    class Meta:
        model  = User
        fields = [
            "id", "email", "full_name", "role", "avatar_url",
            "is_email_verified", "onboarding_completed", "onboarding_step",
            "center_info", "date_joined",
        ]
        read_only_fields = fields

    def get_avatar_url(self, obj):
        request = self.context.get("request")
        if obj.avatar and request:
            return request.build_absolute_uri(obj.avatar.url)
        return None

    def get_center_info(self, obj):
        """
        For clinicians: returns their linked center name and type.
        For hcc_admin/fhc_admin: returns their managed center name.
        For patients: returns None.
        """
        if obj.role == "clinician":
            try:
                cp = obj.clinician_profile
                return {
                    "center_type": cp.center_type,
                    "center_name": cp.center_name,
                    "is_verified": cp.is_verified,
                }
            except Exception:
                return None
        if obj.role == "hcc_admin":
            try:
                return {"center_type": "hcc", "center_name": obj.managed_hcc.name}
            except Exception:
                return None
        if obj.role == "fhc_admin":
            try:
                return {"center_type": "fhc", "center_name": obj.managed_fhc.name}
            except Exception:
                return None
        return None


# ── Email verification ────────────────────────────────────────────────────────

class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()


class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()


# ── Password reset ────────────────────────────────────────────────────────────

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    token    = serializers.CharField()
    password = serializers.CharField(validators=[validate_password])
    confirm_password = serializers.CharField()

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError({"confirm_password": "Passwords do not match."})
        return attrs


# ── Change password (authenticated) ──────────────────────────────────────────

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")
        return value


class ConfirmPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(help_text="Current password to confirm account deletion.")

    def validate_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Password is incorrect.")
        return value


# ── Logout ───────────────────────────────────────────────────────────────────

class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField(help_text="The refresh token to blacklist.")   


# ── Minimal update ────────────────────────────────────────────────────────────

class UpdateProfileSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        required=False,
        allow_null=True,
        error_messages={
            # Shown when Django rejects SVG, corrupted files, non-images
            "invalid_image": "Unsupported file. Please upload a JPEG, PNG, or WebP image."
        }
    )
    full_name = serializers.CharField(required=False, allow_blank=False, min_length=5)

    class Meta:
        model  = User
        fields = ["full_name", "avatar"]

    def validate_avatar(self, value):
        # Only size check here — format already handled above
        return validate_image(value, max_mb=5)


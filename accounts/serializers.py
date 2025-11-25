from django.contrib.auth import authenticate

from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from rest_framework_simplejwt.serializers import TokenObtainPairSerializer


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["is_staff"] = user.is_staff
        token["email"] = user.email

        return token


class AccountLoginSerializer(serializers.Serializer):
    email = serializers.EmailField(
        required=True,
        error_messages={
            "required": "Email is required.",
            "blank": "This field cannot be blank.",
            "invalid": "Please enter a valid email address.",
        },
    )
    password = serializers.CharField(
        write_only=True,
        required=True,
        error_messages={
            "required": "Password is required.",
            "blank": "This field cannot be blank.",
        },
    )

    def validate(self, attrs):
        """
        Validates the email and password, authenticating the user.
        Args:
            attrs (dict): Dictionary containing 'email' and 'password'.
        Returns:
            dict: The validated data with the authenticated user.
        Raises:
            serializers.ValidationError: If email or password is missing or invalid.
        """

        email = attrs.get("email")
        password = attrs.get("password")

        user = authenticate(
            request=self.context.get("request"), email=email, password=password
        )

        if user is None:
            raise ValidationError("Account not found with the given credentials.")

        if not user.is_active:
            raise ValidationError(
                "This account is deactivated. Please contact support."
            )

        attrs["user"] = user
        return attrs

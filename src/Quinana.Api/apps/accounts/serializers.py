"""Validación de los datos que envían los formularios de acceso del sitio Astro."""

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from rest_framework import serializers

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(trim_whitespace=False)
    remember = serializers.BooleanField(default=False)


class RegisterSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=150)
    email = serializers.EmailField(max_length=150)
    password = serializers.CharField(trim_whitespace=False)

    def validate_email(self, value):
        value = value.lower()
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Ya existe una cuenta con este correo.")
        return value

    def validate(self, attrs):
        # Las mismas reglas de contraseña que el resto de Django (AUTH_PASSWORD_VALIDATORS).
        user = User(username=attrs["email"], email=attrs["email"], first_name=attrs["full_name"])
        try:
            validate_password(attrs["password"], user)
        except ValidationError as error:
            raise serializers.ValidationError({"password": list(error.messages)})
        return attrs

    def create(self, validated_data):
        # El correo hace de nombre de usuario: los viajeros inician sesión con su correo.
        return User.objects.create_user(
            username=validated_data["email"],
            email=validated_data["email"],
            password=validated_data["password"],
            first_name=validated_data["full_name"],
        )

"""API de autenticación para los viajeros del sitio público (Astro).

Usa la sesión de Django (cookie `sessionid`, inaccesible para JavaScript) en vez de
tokens. Toda petición que cambia estado exige el token CSRF que entrega CsrfView,
enviado en la cabecera X-CSRFToken.

Los viajeros no reciben permisos sobre el modelo Tour, así que aunque inicien sesión
no pueden entrar al CRUD interno (/tours/ responde 403).
"""

from django.contrib.auth import authenticate, get_user_model, login, logout
from django.middleware.csrf import get_token
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_protect
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import LoginSerializer

User = get_user_model()


def user_data(user):
    return {"email": user.email, "full_name": user.first_name}


class CsrfView(APIView):
    """Entrega el token CSRF (y deja la cookie `csrftoken`) antes de cualquier POST."""

    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"csrfToken": get_token(request)})


@method_decorator(csrf_protect, name="dispatch")
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        account = User.objects.filter(email__iexact=data["email"]).first()
        user = account and authenticate(
            request, username=account.username, password=data["password"]
        )
        if not user:
            # Mismo mensaje si el correo no existe o la contraseña falla: no revela qué cuentas hay.
            return Response(
                {"detail": "Correo o contraseña incorrectos."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        if not data["remember"]:
            request.session.set_expiry(0)  # la sesión termina al cerrar el navegador
        return Response(user_data(user))


@method_decorator(csrf_protect, name="dispatch")
class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        logout(request)
        return Response(status=status.HTTP_204_NO_CONTENT)


class MeView(APIView):
    """Usuario de la sesión actual, o null si no hay sesión."""

    permission_classes = [AllowAny]

    def get(self, request):
        user = request.user
        return Response({"user": user_data(user) if user.is_authenticated else None})

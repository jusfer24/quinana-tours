from django.urls import path

from .views import CsrfView, LoginView, LogoutView, MeView, RegisterView

urlpatterns = [
    path("csrf/", CsrfView.as_view(), name="api_csrf"),
    path("login/", LoginView.as_view(), name="api_login"),
    path("register/", RegisterView.as_view(), name="api_register"),
    path("logout/", LogoutView.as_view(), name="api_logout"),
    path("me/", MeView.as_view(), name="api_me"),
]

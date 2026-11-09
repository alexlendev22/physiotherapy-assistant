from django.contrib import admin
from django.contrib.auth.views import LoginView
from django.urls import include, path
from django.views.generic import RedirectView

from apps.core.forms import LoginForm

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="scheduling:agenda", permanent=False)),
    path("admin/", admin.site.urls),
    path("cuentas/login/", LoginView.as_view(authentication_form=LoginForm), name="login"),
    path("cuentas/", include("django.contrib.auth.urls")),
    path("agenda/", include("apps.scheduling.urls")),
    path("pacientes/", include("apps.patients.urls")),
    path("", include("apps.booking.urls")),
]

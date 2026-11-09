import secrets
from datetime import timedelta

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.models import TimeStampedModel


def generate_token():
    return secrets.token_urlsafe(24)


def default_expiry():
    return timezone.now() + timedelta(days=settings.INVITATION_DEFAULT_EXPIRY_DAYS)


class Invitation(TimeStampedModel):
    """Enlace que se envía al paciente para que reserve una cita por su cuenta."""

    token = models.CharField(max_length=64, unique=True, default=generate_token, editable=False)
    patient = models.ForeignKey(
        "patients.Patient",
        verbose_name="paciente",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="invitations",
        help_text="Opcional. Si lo dejas vacío, el paciente rellenará sus datos al reservar.",
    )
    label = models.CharField("descripción", max_length=100, blank=True, help_text="Ej.: Primera valoración")
    duration_minutes = models.PositiveSmallIntegerField(
        "duración (minutos)", default=60, validators=[MinValueValidator(15), MaxValueValidator(240)]
    )
    expires_at = models.DateTimeField("caduca", default=default_expiry)
    max_uses = models.PositiveSmallIntegerField("usos máximos", default=1, validators=[MinValueValidator(1)])
    uses = models.PositiveSmallIntegerField("usos", default=0, editable=False)
    is_active = models.BooleanField("activa", default=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, editable=False, related_name="+"
    )

    class Meta:
        verbose_name = "invitación"
        verbose_name_plural = "invitaciones"
        ordering = ["-created_at"]

    def __str__(self):
        return self.label or f"Invitación {self.token[:8]}"

    def get_absolute_url(self):
        return reverse("booking:book", args=[self.token])

    @property
    def duration(self):
        return timedelta(minutes=self.duration_minutes)

    @property
    def is_usable(self):
        return self.is_active and self.uses < self.max_uses and self.expires_at > timezone.now()

    @property
    def status_label(self):
        if not self.is_active:
            return "Desactivada"
        if self.uses >= self.max_uses:
            return "Usada"
        if self.expires_at <= timezone.now():
            return "Caducada"
        return "Activa"

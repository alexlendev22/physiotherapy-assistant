from django.core.validators import MaxValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.core.fields import EncryptedTextField
from apps.core.models import TimeStampedModel


class Patient(TimeStampedModel):
    class Sex(models.TextChoices):
        FEMALE = "F", "Mujer"
        MALE = "M", "Hombre"
        OTHER = "O", "Otro"

    first_name = models.CharField("nombre", max_length=100)
    last_name = models.CharField("apellidos", max_length=150)
    national_id = models.CharField("DNI/NIE", max_length=20, blank=True)
    birth_date = models.DateField("fecha de nacimiento", null=True, blank=True)
    sex = models.CharField("sexo", max_length=1, choices=Sex.choices, blank=True)
    phone = models.CharField("teléfono", max_length=30, blank=True)
    email = models.EmailField("email", blank=True)
    address = models.CharField("dirección", max_length=255, blank=True)
    occupation = models.CharField("profesión", max_length=100, blank=True)
    emergency_contact_name = models.CharField("contacto de emergencia", max_length=150, blank=True)
    emergency_contact_phone = models.CharField("teléfono de emergencia", max_length=30, blank=True)
    gdpr_consent = models.BooleanField("consentimiento RGPD", default=False)
    gdpr_consent_at = models.DateTimeField("fecha del consentimiento", null=True, blank=True, editable=False)
    is_active = models.BooleanField("activo", default=True, help_text="Desmárcalo para archivar al paciente.")

    class Meta:
        verbose_name = "paciente"
        verbose_name_plural = "pacientes"
        ordering = ["last_name", "first_name"]
        indexes = [models.Index(fields=["last_name", "first_name"])]

    def __str__(self):
        return self.full_name

    def save(self, *args, **kwargs):
        if self.gdpr_consent and not self.gdpr_consent_at:
            self.gdpr_consent_at = timezone.now()
        elif not self.gdpr_consent:
            self.gdpr_consent_at = None
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("patients:detail", args=[self.pk])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def age(self):
        if not self.birth_date:
            return None
        today = timezone.localdate()
        birthday_pending = (today.month, today.day) < (self.birth_date.month, self.birth_date.day)
        return today.year - self.birth_date.year - birthday_pending


class MedicalHistory(TimeStampedModel):
    """Anamnesis del paciente. Todos los campos clínicos se guardan cifrados."""

    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="medical_history")
    main_complaint = EncryptedTextField("motivo de consulta", blank=True)
    medical_background = EncryptedTextField("antecedentes médicos", blank=True)
    surgeries = EncryptedTextField("cirugías", blank=True)
    medications = EncryptedTextField("medicación actual", blank=True)
    allergies = EncryptedTextField("alergias", blank=True)
    lifestyle = EncryptedTextField("hábitos y actividad física", blank=True)
    observations = EncryptedTextField("observaciones", blank=True)

    class Meta:
        verbose_name = "historial clínico"
        verbose_name_plural = "historiales clínicos"

    def __str__(self):
        return f"Historial de {self.patient}"


class SessionNote(TimeStampedModel):
    """Nota de una sesión de tratamiento en formato SOAP."""

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="session_notes")
    appointment = models.OneToOneField(
        "scheduling.Appointment",
        verbose_name="cita",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="session_note",
    )
    date = models.DateField("fecha", default=timezone.localdate)
    pain_level = models.PositiveSmallIntegerField(
        "dolor (EVA 0-10)", null=True, blank=True, validators=[MaxValueValidator(10)]
    )
    subjective = EncryptedTextField("S · subjetivo", blank=True, help_text="Lo que refiere el paciente.")
    objective = EncryptedTextField("O · objetivo", blank=True, help_text="Exploración, pruebas, mediciones.")
    assessment = EncryptedTextField("A · valoración", blank=True, help_text="Interpretación y evolución.")
    plan = EncryptedTextField("P · plan", blank=True, help_text="Tratamiento aplicado y próximos pasos.")

    class Meta:
        verbose_name = "nota de sesión"
        verbose_name_plural = "notas de sesión"
        ordering = ["-date", "-created_at"]

    def __str__(self):
        return f"Sesión {self.date:%d/%m/%Y} · {self.patient}"

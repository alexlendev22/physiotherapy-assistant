from django.core.exceptions import ValidationError
from django.db import models
from django.urls import reverse

from apps.core.models import TimeStampedModel


class WorkingHours(models.Model):
    """Franja de horario laboral semanal (puede haber varias por día, p. ej. mañana y tarde)."""

    class Weekday(models.IntegerChoices):
        MONDAY = 0, "Lunes"
        TUESDAY = 1, "Martes"
        WEDNESDAY = 2, "Miércoles"
        THURSDAY = 3, "Jueves"
        FRIDAY = 4, "Viernes"
        SATURDAY = 5, "Sábado"
        SUNDAY = 6, "Domingo"

    weekday = models.PositiveSmallIntegerField("día", choices=Weekday.choices)
    start_time = models.TimeField("desde")
    end_time = models.TimeField("hasta")

    class Meta:
        verbose_name = "franja horaria"
        verbose_name_plural = "horario laboral"
        ordering = ["weekday", "start_time"]

    def __str__(self):
        return f"{self.get_weekday_display()} {self.start_time:%H:%M}-{self.end_time:%H:%M}"

    def clean(self):
        if self.start_time and self.end_time and self.end_time <= self.start_time:
            raise ValidationError({"end_time": "La hora de fin debe ser posterior a la de inicio."})


class TimeOff(models.Model):
    """Periodo bloqueado: vacaciones, formación, festivos..."""

    start = models.DateTimeField("desde")
    end = models.DateTimeField("hasta")
    reason = models.CharField("motivo", max_length=150, blank=True)

    class Meta:
        verbose_name = "bloqueo"
        verbose_name_plural = "bloqueos"
        ordering = ["-start"]

    def __str__(self):
        return self.reason or f"Bloqueo {self.start:%d/%m/%Y}"

    def clean(self):
        if self.start and self.end and self.end <= self.start:
            raise ValidationError({"end": "La fecha de fin debe ser posterior a la de inicio."})


class AppointmentQuerySet(models.QuerySet):
    def active(self):
        return self.exclude(status=Appointment.Status.CANCELLED)

    def overlapping(self, start, end):
        return self.active().filter(start__lt=end, end__gt=start)


class Appointment(TimeStampedModel):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendiente"
        CONFIRMED = "confirmed", "Confirmada"
        COMPLETED = "completed", "Realizada"
        NO_SHOW = "no_show", "No se presentó"
        CANCELLED = "cancelled", "Cancelada"

    class Source(models.TextChoices):
        MANUAL = "manual", "Manual"
        INVITATION = "invitation", "Invitación"

    STATUS_COLORS = {
        Status.PENDING: "#f0ad4e",
        Status.CONFIRMED: "#0d6efd",
        Status.COMPLETED: "#198754",
        Status.NO_SHOW: "#dc3545",
        Status.CANCELLED: "#6c757d",
    }

    patient = models.ForeignKey(
        "patients.Patient", verbose_name="paciente", on_delete=models.CASCADE, related_name="appointments"
    )
    start = models.DateTimeField("inicio")
    end = models.DateTimeField("fin")
    status = models.CharField("estado", max_length=20, choices=Status.choices, default=Status.CONFIRMED)
    reason = models.CharField("motivo", max_length=200, blank=True)
    notes = models.TextField("notas internas", blank=True, help_text="Notas administrativas, no clínicas.")
    source = models.CharField("origen", max_length=20, choices=Source.choices, default=Source.MANUAL, editable=False)

    objects = AppointmentQuerySet.as_manager()

    class Meta:
        verbose_name = "cita"
        verbose_name_plural = "citas"
        ordering = ["start"]
        indexes = [models.Index(fields=["start", "end"])]

    def __str__(self):
        return f"{self.start:%d/%m/%Y %H:%M} · {self.patient}"

    def get_absolute_url(self):
        return reverse("scheduling:appointment_update", args=[self.pk])

    def clean(self):
        if not (self.start and self.end):
            return
        if self.end <= self.start:
            raise ValidationError({"end": "La hora de fin debe ser posterior a la de inicio."})
        if self.status != self.Status.CANCELLED:
            clashes = Appointment.objects.overlapping(self.start, self.end).exclude(pk=self.pk)
            if clashes.exists():
                raise ValidationError("Ya hay otra cita en ese horario.")

    @property
    def title(self):
        return f"{self.patient.full_name} · {self.reason}" if self.reason else self.patient.full_name

    @property
    def color(self):
        return self.STATUS_COLORS[self.status]

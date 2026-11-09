from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.booking.models import Invitation
from apps.patients.models import MedicalHistory, Patient, SessionNote
from apps.scheduling.models import Appointment, WorkingHours

DEMO_PATIENTS = [
    ("Ana", "García López", "612345678", "ana@example.com", "Lumbalgia mecánica"),
    ("Luis", "Pérez Martín", "623456789", "luis@example.com", "Esguince de tobillo"),
    ("Marta", "Sánchez Ruiz", "634567890", "marta@example.com", "Cervicalgia"),
    ("Javier", "Romero Díaz", "645678901", "javier@example.com", "Tendinopatía rotuliana"),
]


class Command(BaseCommand):
    help = "Carga datos de demostración: usuario fisio/fisio1234, horario, pacientes, citas e invitación."

    def handle(self, *args, **options):
        User = get_user_model()
        if not User.objects.filter(username="fisio").exists():
            User.objects.create_superuser("fisio", "fisio@example.com", "fisio1234")
            self.stdout.write("Usuario creado: fisio / fisio1234")

        if not WorkingHours.objects.exists():
            for weekday in range(5):
                WorkingHours.objects.create(weekday=weekday, start_time=time(9), end_time=time(14))
                WorkingHours.objects.create(weekday=weekday, start_time=time(16), end_time=time(20))

        if Patient.objects.exists():
            self.stdout.write("Ya hay pacientes; no se crean datos de ejemplo.")
            return

        today = timezone.localdate()
        monday = today - timedelta(days=today.weekday())
        for index, (first_name, last_name, phone, email, complaint) in enumerate(DEMO_PATIENTS):
            patient = Patient.objects.create(
                first_name=first_name, last_name=last_name, phone=phone, email=email, gdpr_consent=True
            )
            MedicalHistory.objects.create(patient=patient, main_complaint=complaint, allergies="Ninguna conocida")

            past_start = timezone.make_aware(datetime.combine(monday - timedelta(days=7 - index), time(10)))
            past = Appointment.objects.create(
                patient=patient,
                start=past_start,
                end=past_start + timedelta(hours=1),
                status=Appointment.Status.COMPLETED,
                reason=complaint,
            )
            SessionNote.objects.create(
                patient=patient,
                appointment=past,
                date=timezone.localdate(past_start),
                pain_level=6 - index,
                subjective=f"Refiere dolor por {complaint.lower()}.",
                objective="Movilidad reducida, palpación dolorosa.",
                assessment="Evolución favorable.",
                plan="Terapia manual + ejercicio terapéutico. Revisar en una semana.",
            )

            next_start = timezone.make_aware(datetime.combine(monday + timedelta(days=index), time(9 + index * 2)))
            Appointment.objects.create(
                patient=patient,
                start=next_start,
                end=next_start + timedelta(hours=1),
                reason="Revisión",
            )

        Invitation.objects.create(label="Primera valoración", duration_minutes=60, max_uses=5)
        self.stdout.write(self.style.SUCCESS("Datos de demostración creados."))

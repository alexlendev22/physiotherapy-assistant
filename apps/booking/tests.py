from datetime import datetime, time, timedelta

from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from apps.patients.models import Patient
from apps.scheduling.models import Appointment, WorkingHours

from .models import Invitation


@override_settings(BOOKING_SLOT_STEP_MINUTES=30, BOOKING_MIN_NOTICE_HOURS=12, BOOKING_MAX_DAYS_AHEAD=30)
class PublicBookingTests(TestCase):
    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=7)
        WorkingHours.objects.create(weekday=self.day.weekday(), start_time=time(9), end_time=time(12))
        self.invitation = Invitation.objects.create(duration_minutes=60)
        self.url = reverse("booking:book", args=[self.invitation.token])
        self.slot = timezone.make_aware(datetime.combine(self.day, time(10)))

    def post_booking(self, **overrides):
        data = {
            "fecha": self.day.isoformat(),
            "slot": self.slot.isoformat(),
            "first_name": "Ana",
            "last_name": "García",
            "phone": "600000000",
            "email": "ana@example.com",
            "gdpr_consent": "on",
        }
        data.update(overrides)
        return self.client.post(self.url, data)

    def test_booking_page_is_public(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Reserva tu cita")

    def test_booking_creates_patient_and_appointment(self):
        response = self.post_booking()

        self.assertRedirects(response, reverse("booking:done", args=[self.invitation.token]))
        appointment = Appointment.objects.get()
        self.assertEqual(appointment.start, self.slot)
        self.assertEqual(appointment.end, self.slot + timedelta(hours=1))
        self.assertEqual(appointment.source, Appointment.Source.INVITATION)
        self.assertEqual(appointment.patient.full_name, "Ana García")
        self.assertTrue(appointment.patient.gdpr_consent)
        self.invitation.refresh_from_db()
        self.assertEqual(self.invitation.uses, 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_invitation_for_existing_patient_skips_personal_data(self):
        patient = Patient.objects.create(first_name="Luis", last_name="Pérez", email="luis@example.com")
        self.invitation.patient = patient
        self.invitation.save()

        response = self.client.post(self.url, {"fecha": self.day.isoformat(), "slot": self.slot.isoformat()})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(Appointment.objects.get().patient, patient)
        self.assertEqual(Patient.objects.count(), 1)

    def test_used_invitation_cannot_be_reused(self):
        self.post_booking()
        response = self.post_booking(slot=(self.slot + timedelta(hours=1)).isoformat())

        self.assertEqual(response.status_code, 404)
        self.assertEqual(Appointment.objects.count(), 1)

    def test_unavailable_slot_is_rejected(self):
        response = self.post_booking(slot=timezone.make_aware(datetime.combine(self.day, time(14))).isoformat())

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ya no está disponible")
        self.assertFalse(Appointment.objects.exists())

    def test_expired_invitation_is_rejected(self):
        self.invitation.expires_at = timezone.now() - timedelta(minutes=1)
        self.invitation.save()

        self.assertEqual(self.client.get(self.url).status_code, 404)

    def test_unknown_token_is_rejected(self):
        response = self.client.get(reverse("booking:book", args=["no-existe"]))
        self.assertEqual(response.status_code, 404)

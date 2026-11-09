from datetime import datetime, time, timedelta

from django.core.exceptions import ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from apps.patients.models import Patient

from .models import Appointment, TimeOff, WorkingHours
from .services import available_slots, is_slot_available


@override_settings(BOOKING_SLOT_STEP_MINUTES=30, BOOKING_MIN_NOTICE_HOURS=12, BOOKING_MAX_DAYS_AHEAD=30)
class AvailableSlotsTests(TestCase):
    def setUp(self):
        self.day = timezone.localdate() + timedelta(days=7)
        self.duration = timedelta(hours=1)
        WorkingHours.objects.create(weekday=self.day.weekday(), start_time=time(9), end_time=time(11))
        self.patient = Patient.objects.create(first_name="Ana", last_name="García")

    def at(self, hour, minute=0):
        return timezone.make_aware(datetime.combine(self.day, time(hour, minute)))

    def test_slots_follow_working_hours(self):
        self.assertEqual(available_slots(self.day, self.duration), [self.at(9), self.at(9, 30), self.at(10)])

    def test_no_slots_outside_working_days(self):
        self.assertEqual(available_slots(self.day + timedelta(days=1), self.duration), [])

    def test_appointment_blocks_overlapping_slots(self):
        Appointment.objects.create(patient=self.patient, start=self.at(10), end=self.at(11))
        self.assertEqual(available_slots(self.day, self.duration), [self.at(9)])

    def test_cancelled_appointment_frees_slots(self):
        Appointment.objects.create(
            patient=self.patient, start=self.at(10), end=self.at(11), status=Appointment.Status.CANCELLED
        )
        self.assertEqual(len(available_slots(self.day, self.duration)), 3)

    def test_time_off_blocks_slots(self):
        TimeOff.objects.create(start=self.at(9), end=self.at(10))
        self.assertEqual(available_slots(self.day, self.duration), [self.at(10)])

    def test_minimum_notice_is_respected(self):
        now = self.at(9) - timedelta(hours=12) + timedelta(minutes=1)
        self.assertEqual(available_slots(self.day, self.duration, now=now), [self.at(9, 30), self.at(10)])

    def test_is_slot_available(self):
        self.assertTrue(is_slot_available(self.at(9, 30), self.duration))
        self.assertFalse(is_slot_available(self.at(9, 15), self.duration))
        self.assertFalse(is_slot_available(self.at(10, 30), self.duration))


class AppointmentValidationTests(TestCase):
    def test_overlapping_appointment_is_rejected(self):
        patient = Patient.objects.create(first_name="Ana", last_name="García")
        start = timezone.now() + timedelta(days=1)
        Appointment.objects.create(patient=patient, start=start, end=start + timedelta(hours=1))

        clash = Appointment(patient=patient, start=start + timedelta(minutes=30), end=start + timedelta(hours=2))

        with self.assertRaises(ValidationError):
            clash.full_clean()

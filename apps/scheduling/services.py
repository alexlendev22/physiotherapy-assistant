"""Cálculo de disponibilidad para las reservas."""

from datetime import datetime, time, timedelta

from django.conf import settings
from django.utils import timezone

from .models import Appointment, TimeOff, WorkingHours


def _aware(day, at):
    return timezone.make_aware(datetime.combine(day, at))


def available_slots(day, duration, *, now=None):
    """Devuelve las horas de inicio libres de `day` para una cita de `duration`."""
    now = now or timezone.now()
    earliest = now + timedelta(hours=settings.BOOKING_MIN_NOTICE_HOURS)
    step = timedelta(minutes=settings.BOOKING_SLOT_STEP_MINUTES)

    day_start = _aware(day, time.min)
    day_end = day_start + timedelta(days=1)
    busy = list(Appointment.objects.overlapping(day_start, day_end).values_list("start", "end"))
    busy += TimeOff.objects.filter(start__lt=day_end, end__gt=day_start).values_list("start", "end")

    slots = []
    for block in WorkingHours.objects.filter(weekday=day.weekday()):
        cursor = _aware(day, block.start_time)
        block_end = _aware(day, block.end_time)
        while cursor + duration <= block_end:
            slot_end = cursor + duration
            if cursor >= earliest and not any(start < slot_end and cursor < end for start, end in busy):
                slots.append(cursor)
            cursor += step
    return slots


def available_days(duration, *, now=None):
    """Días (dentro del horizonte de reserva) que tienen al menos un hueco libre."""
    today = timezone.localdate(now or timezone.now())
    days = (today + timedelta(days=offset) for offset in range(settings.BOOKING_MAX_DAYS_AHEAD + 1))
    return [day for day in days if available_slots(day, duration, now=now)]


def is_slot_available(start, duration, *, now=None):
    day = timezone.localdate(start)
    today = timezone.localdate(now or timezone.now())
    if day > today + timedelta(days=settings.BOOKING_MAX_DAYS_AHEAD):
        return False
    return start in available_slots(day, duration, now=now)

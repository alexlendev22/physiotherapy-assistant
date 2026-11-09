from datetime import timedelta

from django.conf import settings
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.forms import modelformset_factory
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView, UpdateView

from .forms import AppointmentForm, TimeOffForm, WorkingHoursForm
from .models import Appointment, TimeOff, WorkingHours


def _parse_query_datetime(value):
    # El "+" del offset horario puede llegar convertido en espacio en la query string.
    try:
        parsed = parse_datetime((value or "").replace(" ", "+"))
    except ValueError:
        return None
    if parsed is not None and timezone.is_naive(parsed):
        parsed = timezone.make_aware(parsed)
    return parsed


def agenda(request):
    business_hours = [
        {
            # FullCalendar numera los días desde el domingo (0); nosotros desde el lunes.
            "daysOfWeek": [(block.weekday + 1) % 7],
            "startTime": block.start_time.strftime("%H:%M"),
            "endTime": block.end_time.strftime("%H:%M"),
        }
        for block in WorkingHours.objects.all()
    ]
    return render(request, "scheduling/agenda.html", {"business_hours": business_hours})


def appointment_events(request):
    """Feed JSON para FullCalendar."""
    start = _parse_query_datetime(request.GET.get("start"))
    end = _parse_query_datetime(request.GET.get("end"))
    if not (start and end):
        return HttpResponseBadRequest("Parámetros start/end inválidos.")

    events = [
        {
            "id": appointment.pk,
            "title": appointment.title,
            "start": appointment.start.isoformat(),
            "end": appointment.end.isoformat(),
            "url": appointment.get_absolute_url(),
            "color": appointment.color,
        }
        for appointment in Appointment.objects.overlapping(start, end).select_related("patient")
    ]
    events += [
        {
            "title": time_off.reason,
            "start": time_off.start.isoformat(),
            "end": time_off.end.isoformat(),
            "display": "background",
            "color": "#adb5bd",
        }
        for time_off in TimeOff.objects.filter(start__lt=end, end__gt=start)
    ]
    return JsonResponse(events, safe=False)


class AppointmentCreateView(SuccessMessageMixin, CreateView):
    model = Appointment
    form_class = AppointmentForm
    success_url = reverse_lazy("scheduling:agenda")
    success_message = "Cita creada."

    def get_initial(self):
        initial = super().get_initial()
        start = _parse_query_datetime(self.request.GET.get("start"))
        end = _parse_query_datetime(self.request.GET.get("end"))
        if start:
            initial["start"] = start
            initial["end"] = end if end and end > start else start + timedelta(
                minutes=settings.DEFAULT_APPOINTMENT_MINUTES
            )
        if patient_id := self.request.GET.get("paciente"):
            initial["patient"] = patient_id
        return initial


class AppointmentUpdateView(SuccessMessageMixin, UpdateView):
    model = Appointment
    form_class = AppointmentForm
    success_url = reverse_lazy("scheduling:agenda")
    success_message = "Cita actualizada."


WorkingHoursFormSet = modelformset_factory(WorkingHours, form=WorkingHoursForm, extra=2, can_delete=True)


def working_hours(request):
    formset = WorkingHoursFormSet(request.POST or None, queryset=WorkingHours.objects.all())
    if request.method == "POST" and formset.is_valid():
        formset.save()
        messages.success(request, "Horario guardado.")
        return redirect("scheduling:working_hours")
    return render(request, "scheduling/working_hours.html", {"formset": formset})


class TimeOffListView(ListView):
    model = TimeOff
    paginate_by = 25

    def get_queryset(self):
        return TimeOff.objects.filter(end__gte=timezone.now()).order_by("start")


class TimeOffCreateView(SuccessMessageMixin, CreateView):
    model = TimeOff
    form_class = TimeOffForm
    success_url = reverse_lazy("scheduling:timeoff_list")
    success_message = "Bloqueo creado."


@require_POST
def timeoff_delete(request, pk):
    get_object_or_404(TimeOff, pk=pk).delete()
    messages.success(request, "Bloqueo eliminado.")
    return redirect("scheduling:timeoff_list")

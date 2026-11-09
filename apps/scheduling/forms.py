from django import forms
from django.db.models import Q

from apps.core.forms import BootstrapFormMixin, DateTimeInput, TimeInput
from apps.patients.models import Patient

from .models import Appointment, TimeOff, WorkingHours


class AppointmentForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["patient", "start", "end", "status", "reason", "notes"]
        widgets = {
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pacientes activos, más el de la cita si ya estaba archivado.
        self.fields["patient"].queryset = Patient.objects.filter(
            Q(is_active=True) | Q(pk=self.instance.patient_id)
        )


class WorkingHoursForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = WorkingHours
        fields = ["weekday", "start_time", "end_time"]
        widgets = {"start_time": TimeInput(), "end_time": TimeInput()}


class TimeOffForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = TimeOff
        fields = ["start", "end", "reason"]
        widgets = {"start": DateTimeInput(), "end": DateTimeInput()}

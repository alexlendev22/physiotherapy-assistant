from django import forms

from apps.core.forms import BootstrapFormMixin, DateInput

from .models import MedicalHistory, Patient, SessionNote


class PatientForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "first_name",
            "last_name",
            "national_id",
            "birth_date",
            "sex",
            "phone",
            "email",
            "occupation",
            "address",
            "emergency_contact_name",
            "emergency_contact_phone",
            "gdpr_consent",
            "is_active",
        ]
        widgets = {"birth_date": DateInput()}


class MedicalHistoryForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = MedicalHistory
        exclude = ["patient"]
        widgets = {
            name: forms.Textarea(attrs={"rows": 3})
            for name in [
                "main_complaint",
                "medical_background",
                "surgeries",
                "medications",
                "allergies",
                "lifestyle",
                "observations",
            ]
        }


class SessionNoteForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = SessionNote
        fields = ["date", "appointment", "pain_level", "subjective", "objective", "assessment", "plan"]
        widgets = {
            "date": DateInput(),
            "subjective": forms.Textarea(attrs={"rows": 3}),
            "objective": forms.Textarea(attrs={"rows": 3}),
            "assessment": forms.Textarea(attrs={"rows": 3}),
            "plan": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, patient, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["appointment"].queryset = patient.appointments.exclude(status="cancelled").order_by("-start")

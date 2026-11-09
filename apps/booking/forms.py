from django import forms

from apps.core.forms import BootstrapFormMixin, DateTimeInput
from apps.patients.models import Patient

from .models import Invitation


class InvitationForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = Invitation
        fields = ["patient", "label", "duration_minutes", "expires_at", "max_uses"]
        widgets = {"expires_at": DateTimeInput()}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["patient"].queryset = Patient.objects.filter(is_active=True)


class PublicBookingForm(BootstrapFormMixin, forms.Form):
    """Datos que rellena el paciente en la página pública de reserva."""

    NEW_PATIENT_FIELDS = ["first_name", "last_name", "phone", "email", "gdpr_consent"]

    first_name = forms.CharField(label="Nombre", max_length=100)
    last_name = forms.CharField(label="Apellidos", max_length=150)
    phone = forms.CharField(label="Teléfono", max_length=30)
    email = forms.EmailField(label="Email", help_text="Te enviaremos aquí la confirmación.")
    reason = forms.CharField(label="Motivo de la consulta (opcional)", max_length=200, required=False)
    gdpr_consent = forms.BooleanField(
        label="Acepto el tratamiento de mis datos personales y de salud para la gestión de mi atención "
        "fisioterapéutica."
    )

    def __init__(self, *args, invitation, **kwargs):
        super().__init__(*args, **kwargs)
        # Si la invitación ya es para un paciente concreto, no le pedimos sus datos otra vez.
        if invitation.patient_id:
            for name in self.NEW_PATIENT_FIELDS:
                del self.fields[name]

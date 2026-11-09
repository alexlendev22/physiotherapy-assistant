from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.generic import CreateView, DetailView, ListView, UpdateView

from apps.core.fields import EncryptedTextField

from .forms import MedicalHistoryForm, PatientForm, SessionNoteForm
from .models import MedicalHistory, Patient, SessionNote

DETAIL_TABS = [
    ("datos", "Datos personales"),
    ("historial", "Historial clínico"),
    ("sesiones", "Sesiones"),
    ("citas", "Citas"),
]


class PatientListView(ListView):
    model = Patient
    paginate_by = 25

    def get_queryset(self):
        queryset = Patient.objects.all()
        query = self.request.GET.get("q", "").strip()
        if query:
            queryset = queryset.filter(
                Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
                | Q(phone__icontains=query)
                | Q(email__icontains=query)
                | Q(national_id__icontains=query)
            )
        if self.request.GET.get("archivados") != "1":
            queryset = queryset.filter(is_active=True)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["query"] = self.request.GET.get("q", "")
        context["show_archived"] = self.request.GET.get("archivados") == "1"
        return context


class PatientCreateView(SuccessMessageMixin, CreateView):
    model = Patient
    form_class = PatientForm
    success_message = "Paciente creado."


class PatientUpdateView(SuccessMessageMixin, UpdateView):
    model = Patient
    form_class = PatientForm
    success_message = "Datos del paciente actualizados."


class PatientDetailView(DetailView):
    model = Patient

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        patient = self.object
        history = MedicalHistory.objects.filter(patient=patient).first()
        now = timezone.now()
        appointments = patient.appointments.order_by("start")
        tab = self.request.GET.get("tab", "datos")
        context.update(
            tabs=DETAIL_TABS,
            tab=tab if tab in dict(DETAIL_TABS) else "datos",
            history_fields=[
                (field.verbose_name, getattr(history, field.name))
                for field in MedicalHistory._meta.get_fields()
                if isinstance(field, EncryptedTextField)
            ]
            if history
            else [],
            session_notes=patient.session_notes.select_related("appointment"),
            upcoming_appointments=appointments.filter(start__gte=now),
            past_appointments=appointments.filter(start__lt=now).reverse()[:20],
        )
        return context


def medical_history_edit(request, pk):
    patient = get_object_or_404(Patient, pk=pk)
    history = MedicalHistory.objects.filter(patient=patient).first() or MedicalHistory(patient=patient)
    form = MedicalHistoryForm(request.POST or None, instance=history)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Historial clínico guardado.")
        return redirect(f"{patient.get_absolute_url()}?tab=historial")
    return render(request, "patients/medical_history_form.html", {"form": form, "patient": patient})


class PatientSessionNoteMixin:
    model = SessionNote
    form_class = SessionNoteForm

    def dispatch(self, request, *args, **kwargs):
        self.patient = get_object_or_404(Patient, pk=kwargs["pk"])
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["patient"] = self.patient
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient"] = self.patient
        return context

    def get_success_url(self):
        return f"{self.patient.get_absolute_url()}?tab=sesiones"


class SessionNoteCreateView(PatientSessionNoteMixin, SuccessMessageMixin, CreateView):
    success_message = "Sesión registrada."

    def get_initial(self):
        initial = super().get_initial()
        appointment_id = self.request.GET.get("cita")
        if appointment_id:
            appointment = self.patient.appointments.filter(pk=appointment_id).first()
            if appointment:
                initial["appointment"] = appointment
                initial["date"] = timezone.localdate(appointment.start)
        return initial

    def form_valid(self, form):
        form.instance.patient = self.patient
        return super().form_valid(form)


class SessionNoteUpdateView(PatientSessionNoteMixin, SuccessMessageMixin, UpdateView):
    pk_url_kwarg = "note_pk"
    success_message = "Sesión actualizada."

    def get_queryset(self):
        return SessionNote.objects.filter(patient=self.patient)

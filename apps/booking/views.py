from django.contrib import messages
from django.contrib.auth.decorators import login_not_required
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from django.views.decorators.http import require_POST
from django.views.generic import CreateView, ListView

from apps.scheduling.models import Appointment
from apps.scheduling.services import available_days, available_slots

from .forms import InvitationForm, PublicBookingForm
from .models import Invitation
from .services import BookingError, create_booking, send_booking_confirmation

BOOKED_APPOINTMENT_SESSION_KEY = "booked_appointment_id"


# --- Panel del fisio -------------------------------------------------------


class InvitationListView(ListView):
    model = Invitation
    paginate_by = 25

    def get_queryset(self):
        return Invitation.objects.select_related("patient")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        invitations = list(context["object_list"])
        for invitation in invitations:
            invitation.public_url = self.request.build_absolute_uri(invitation.get_absolute_url())
        context["invitations"] = invitations
        return context


class InvitationCreateView(SuccessMessageMixin, CreateView):
    model = Invitation
    form_class = InvitationForm
    success_url = reverse_lazy("booking:invitation_list")
    success_message = "Invitación creada. Copia el enlace y envíaselo al paciente."

    def get_initial(self):
        initial = super().get_initial()
        if patient_id := self.request.GET.get("paciente"):
            initial["patient"] = patient_id
        return initial

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


@require_POST
def invitation_deactivate(request, pk):
    invitation = get_object_or_404(Invitation, pk=pk)
    invitation.is_active = False
    invitation.save(update_fields=["is_active", "updated_at"])
    messages.success(request, "Invitación desactivada.")
    return redirect("booking:invitation_list")


# --- Página pública de reserva ---------------------------------------------


def _safe_parse(parser, value):
    try:
        return parser(value or "")
    except ValueError:
        return None


@login_not_required
def book(request, token):
    invitation = Invitation.objects.select_related("patient").filter(token=token).first()
    if invitation is None or not invitation.is_usable:
        return render(request, "booking/invalid.html", status=404)

    days = available_days(invitation.duration)
    selected_day = _safe_parse(parse_date, request.GET.get("fecha") or request.POST.get("fecha"))
    if selected_day not in days:
        selected_day = days[0] if days else None

    slot_error = None
    if request.method == "POST":
        form = PublicBookingForm(request.POST, invitation=invitation)
        start = _safe_parse(parse_datetime, request.POST.get("slot"))
        if start is None or timezone.is_naive(start):
            slot_error = "Elige una hora disponible."
        if form.is_valid() and not slot_error:
            try:
                appointment = create_booking(invitation.pk, start, form.cleaned_data)
            except BookingError as exc:
                slot_error = str(exc)
            else:
                send_booking_confirmation(appointment)
                request.session[BOOKED_APPOINTMENT_SESSION_KEY] = appointment.pk
                return redirect("booking:done", token=token)
    else:
        form = PublicBookingForm(invitation=invitation)

    return render(
        request,
        "booking/book.html",
        {
            "invitation": invitation,
            "days": days,
            "selected_day": selected_day,
            "slots": available_slots(selected_day, invitation.duration) if selected_day else [],
            "selected_slot": request.POST.get("slot", ""),
            "slot_error": slot_error,
            "form": form,
        },
    )


@login_not_required
def booking_done(request, token):
    appointment_id = request.session.get(BOOKED_APPOINTMENT_SESSION_KEY)
    appointment = Appointment.objects.filter(pk=appointment_id).first() if appointment_id else None
    if appointment is None:
        return redirect("booking:book", token=token)
    return render(request, "booking/done.html", {"appointment": appointment})

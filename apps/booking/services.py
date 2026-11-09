import logging

from django.core.mail import send_mail
from django.db import transaction
from django.template.loader import render_to_string

from apps.patients.models import Patient
from apps.scheduling.models import Appointment
from apps.scheduling.services import is_slot_available

from .models import Invitation

logger = logging.getLogger(__name__)


class BookingError(Exception):
    pass


@transaction.atomic
def create_booking(invitation_id, start, data):
    """Crea la cita de una invitación, revalidando todo dentro de la transacción."""
    invitation = Invitation.objects.select_for_update().select_related("patient").get(pk=invitation_id)
    if not invitation.is_usable:
        raise BookingError("Este enlace de reserva ya no es válido.")
    if not is_slot_available(start, invitation.duration):
        raise BookingError("Esa hora ya no está disponible. Elige otra, por favor.")

    patient = invitation.patient or Patient.objects.create(
        first_name=data["first_name"],
        last_name=data["last_name"],
        phone=data["phone"],
        email=data["email"],
        gdpr_consent=data["gdpr_consent"],
    )
    appointment = Appointment.objects.create(
        patient=patient,
        start=start,
        end=start + invitation.duration,
        status=Appointment.Status.CONFIRMED,
        reason=data.get("reason") or invitation.label,
        source=Appointment.Source.INVITATION,
    )
    invitation.uses += 1
    invitation.save(update_fields=["uses", "updated_at"])
    return appointment


def send_booking_confirmation(appointment):
    patient = appointment.patient
    if not patient.email:
        return
    body = render_to_string("booking/emails/confirmation.txt", {"appointment": appointment, "patient": patient})
    try:
        send_mail("Confirmación de tu cita de fisioterapia", body, None, [patient.email])
    except Exception:
        # La cita ya está creada; un fallo de email no debe romper la reserva.
        logger.exception("No se pudo enviar la confirmación de la cita %s", appointment.pk)

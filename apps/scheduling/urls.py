from django.urls import path

from . import views

app_name = "scheduling"

urlpatterns = [
    path("", views.agenda, name="agenda"),
    path("eventos/", views.appointment_events, name="events"),
    path("citas/nueva/", views.AppointmentCreateView.as_view(), name="appointment_create"),
    path("citas/<int:pk>/", views.AppointmentUpdateView.as_view(), name="appointment_update"),
    path("horario/", views.working_hours, name="working_hours"),
    path("bloqueos/", views.TimeOffListView.as_view(), name="timeoff_list"),
    path("bloqueos/nuevo/", views.TimeOffCreateView.as_view(), name="timeoff_create"),
    path("bloqueos/<int:pk>/eliminar/", views.timeoff_delete, name="timeoff_delete"),
]

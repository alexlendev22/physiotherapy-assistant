from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.PatientListView.as_view(), name="list"),
    path("nuevo/", views.PatientCreateView.as_view(), name="create"),
    path("<int:pk>/", views.PatientDetailView.as_view(), name="detail"),
    path("<int:pk>/editar/", views.PatientUpdateView.as_view(), name="update"),
    path("<int:pk>/historial/", views.medical_history_edit, name="medical_history"),
    path("<int:pk>/sesiones/nueva/", views.SessionNoteCreateView.as_view(), name="session_create"),
    path("<int:pk>/sesiones/<int:note_pk>/", views.SessionNoteUpdateView.as_view(), name="session_update"),
]

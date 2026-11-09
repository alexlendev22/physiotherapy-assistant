from django.urls import path

from . import views

app_name = "booking"

urlpatterns = [
    path("invitaciones/", views.InvitationListView.as_view(), name="invitation_list"),
    path("invitaciones/nueva/", views.InvitationCreateView.as_view(), name="invitation_create"),
    path("invitaciones/<int:pk>/desactivar/", views.invitation_deactivate, name="invitation_deactivate"),
    # Públicas (sin login)
    path("reservar/<str:token>/", views.book, name="book"),
    path("reservar/<str:token>/confirmada/", views.booking_done, name="done"),
]

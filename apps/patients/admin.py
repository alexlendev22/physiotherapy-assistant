from django.contrib import admin

from .models import MedicalHistory, Patient, SessionNote


class MedicalHistoryInline(admin.StackedInline):
    model = MedicalHistory
    can_delete = False


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "email", "birth_date", "gdpr_consent", "is_active"]
    list_filter = ["is_active", "gdpr_consent", "sex"]
    search_fields = ["first_name", "last_name", "phone", "email", "national_id"]
    readonly_fields = ["gdpr_consent_at", "created_at", "updated_at"]
    inlines = [MedicalHistoryInline]


@admin.register(SessionNote)
class SessionNoteAdmin(admin.ModelAdmin):
    list_display = ["patient", "date", "pain_level"]
    list_select_related = ["patient"]
    search_fields = ["patient__first_name", "patient__last_name"]
    date_hierarchy = "date"
    autocomplete_fields = ["patient"]
    raw_id_fields = ["appointment"]

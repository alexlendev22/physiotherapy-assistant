from django.contrib import admin

from .models import Appointment, TimeOff, WorkingHours


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["start", "end", "patient", "status", "source"]
    list_filter = ["status", "source"]
    list_select_related = ["patient"]
    search_fields = ["patient__first_name", "patient__last_name", "reason"]
    date_hierarchy = "start"
    autocomplete_fields = ["patient"]


@admin.register(WorkingHours)
class WorkingHoursAdmin(admin.ModelAdmin):
    list_display = ["weekday", "start_time", "end_time"]


@admin.register(TimeOff)
class TimeOffAdmin(admin.ModelAdmin):
    list_display = ["start", "end", "reason"]

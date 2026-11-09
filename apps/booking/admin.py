from django.contrib import admin

from .models import Invitation


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ["__str__", "patient", "duration_minutes", "uses", "max_uses", "expires_at", "is_active"]
    list_filter = ["is_active"]
    list_select_related = ["patient"]
    readonly_fields = ["token", "uses", "created_by", "created_at"]
    autocomplete_fields = ["patient"]

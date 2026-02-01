from django.contrib import admin
from .models import Caretaker


@admin.register(Caretaker)
class CaretakerAdmin(admin.ModelAdmin):
    list_display = ['user', 'caretaker', 'end_date', 'created_at']
    list_filter = ['end_date', 'created_at']
    search_fields = ['user__email', 'caretaker__email', 'reason']
    raw_id_fields = ['user', 'caretaker']
    date_hierarchy = 'created_at'

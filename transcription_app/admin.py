from django.contrib import admin
from .models import Transcription

@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    """Admin interface for the Transcription model."""
    list_display = ('id', 'appointment', 'status', 'audio_duration', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('appointment__patient__email', 'appointment__doctor__email')
    readonly_fields = ('id', 'created_at', 'updated_at')

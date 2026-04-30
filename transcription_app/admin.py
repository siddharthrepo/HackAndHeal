from django.contrib import admin
from .models import Transcription, SOAPNote

@admin.register(Transcription)
class TranscriptionAdmin(admin.ModelAdmin):
    """Admin interface for the Transcription model."""
    list_display = ('id', 'appointment', 'status', 'audio_duration', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('appointment__patient__email', 'appointment__doctor__email')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(SOAPNote)
class SOAPNoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'status', 'is_edited', 'created_at')
    list_filter = ('status', 'is_edited', 'created_at')
    search_fields = ('appointment__patient__email', 'appointment__doctor__email')
    readonly_fields = ('id', 'created_at', 'updated_at')

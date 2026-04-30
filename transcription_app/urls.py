from django.urls import path
from .views import (
    TranscriptionCreateView, TranscriptionStatusView, TranscriptionDetailView,
    SOAPNoteDetailView, SOAPNoteEditView, SOAPNoteRegenerateView,
)

urlpatterns = [
    path('create/<uuid:appointment_id>/', TranscriptionCreateView.as_view(), name='create_transcription'),
    path('status/<uuid:transcription_id>/', TranscriptionStatusView.as_view(), name='transcription_status'),
    path('detail/<uuid:pk>/', TranscriptionDetailView.as_view(), name='transcription_detail'),
    path('soap/<uuid:pk>/', SOAPNoteDetailView.as_view(), name='soap_note_detail'),
    path('soap/<uuid:pk>/edit/', SOAPNoteEditView.as_view(), name='soap_note_edit'),
    path('soap/regenerate/<uuid:appointment_id>/', SOAPNoteRegenerateView.as_view(), name='soap_note_regenerate'),
]

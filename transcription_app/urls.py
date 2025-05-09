from django.urls import path
from .views import TranscriptionCreateView, TranscriptionStatusView, TranscriptionDetailView

urlpatterns = [
    path('create/<uuid:appointment_id>/', TranscriptionCreateView.as_view(), name='create_transcription'),
    path('status/<uuid:transcription_id>/', TranscriptionStatusView.as_view(), name='transcription_status'),
    path('detail/<uuid:pk>/', TranscriptionDetailView.as_view(), name='transcription_detail'),
]

import json
import base64
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseBadRequest
from django.core.exceptions import PermissionDenied
from django.utils import timezone
from django.contrib import messages
from consultation_app.models import Appointment
from .models import Transcription
from .services import TranscriptionService

class TranscriptionCreateView(LoginRequiredMixin, View):
    """
    View for creating a transcription from submitted audio data using Deepgram only.
    """
    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        # Check permissions
        if request.user != appointment.doctor and request.user != appointment.patient:
            raise PermissionDenied("You don't have permission to transcribe this appointment.")

        try:
            audio_data = request.FILES.get('audio_data')

            if not audio_data:
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            audio_bytes = audio_data.read()

            transcription, created = Transcription.objects.get_or_create(
                appointment=appointment,
                defaults={'status': Transcription.Status.PENDING}
            )

            if transcription.status == Transcription.Status.FAILED:
                transcription.status = Transcription.Status.PENDING
                transcription.error_message = None
                transcription.save()

            try:
                transcript = TranscriptionService.process_audio(audio_bytes, transcription)
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f"Transcription failed with Deepgram: {str(e)}"
                }, status=500)

            return JsonResponse({
                'success': True,
                'transcription_id': str(transcription.id)
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f"An error occurred: {str(e)}"
            }, status=500)

class TranscriptionStatusView(LoginRequiredMixin, View):
    """
    View for checking the status of a transcription.
    """
    def get(self, request, transcription_id):
        transcription = get_object_or_404(Transcription, id=transcription_id)
        appointment = transcription.appointment
        
        # Check permissions
        if request.user != appointment.doctor and request.user != appointment.patient:
            raise PermissionDenied("You don't have permission to view this transcription.")
        
        return JsonResponse({
            'status': transcription.status,
            'completed': transcription.status == Transcription.Status.COMPLETED,
            'failed': transcription.status == Transcription.Status.FAILED,
            'error_message': transcription.error_message,
            'created_at': transcription.created_at.isoformat(),
            'updated_at': transcription.updated_at.isoformat()
        })

class TranscriptionDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying a transcription.
    """
    model = Transcription
    template_name = 'transcription/detail.html'
    context_object_name = 'transcription'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        appointment = obj.appointment
        
        # Check permissions
        if self.request.user != appointment.doctor and self.request.user != appointment.patient:
            raise PermissionDenied("You don't have permission to view this transcription.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appointment'] = self.object.appointment
        return context

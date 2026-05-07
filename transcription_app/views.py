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
from .models import Transcription, SOAPNote
from .services import TranscriptionService
from .forms import SOAPNoteEditForm

class TranscriptionCreateView(LoginRequiredMixin, View):
    """
    Accepts per-speaker audio uploads (local_audio + remote_audio) and runs them
    through Groq Whisper separately so each speaker can be labeled in the
    merged transcript. Falls back to a single audio_data blob for safety.
    """
    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if request.user != appointment.doctor and request.user != appointment.patient:
            raise PermissionDenied("You don't have permission to transcribe this appointment.")

        try:
            local_file  = request.FILES.get('local_audio')
            remote_file = request.FILES.get('remote_audio')
            legacy_file = request.FILES.get('audio_data')  # backwards-compat
            local_role  = (request.POST.get('local_role') or '').strip().lower()

            if local_role not in ('doctor', 'patient'):
                # Derive from the authenticated user as a fallback.
                local_role = 'doctor' if request.user == appointment.doctor else 'patient'

            local_bytes  = local_file.read()  if local_file  else None
            remote_bytes = remote_file.read() if remote_file else None

            if not local_bytes and not remote_bytes and legacy_file:
                # Single-blob legacy path
                local_bytes = legacy_file.read()

            if not local_bytes and not remote_bytes:
                return JsonResponse({'error': 'No audio data provided'}, status=400)

            transcription, _created = Transcription.objects.get_or_create(
                appointment=appointment,
                defaults={'status': Transcription.Status.PENDING}
            )

            # The other participant may also submit audio — don't reprocess.
            if transcription.status == Transcription.Status.COMPLETED:
                return JsonResponse({
                    'success': True,
                    'message': 'Transcription already completed',
                    'transcription_id': str(transcription.id)
                })

            if transcription.status == Transcription.Status.FAILED:
                transcription.status = Transcription.Status.PENDING
                transcription.error_message = None
                transcription.save()

            try:
                TranscriptionService.process_dual_audio(
                    local_audio=local_bytes,
                    remote_audio=remote_bytes,
                    transcription=transcription,
                    local_role=local_role,
                )
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'error': f"Transcription failed: {str(e)}"
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


class SOAPNoteDetailView(LoginRequiredMixin, View):
    def get(self, request, pk):
        soap_note = get_object_or_404(SOAPNote, pk=pk)
        appointment = soap_note.appointment

        if request.user != appointment.doctor and request.user != appointment.patient:
            raise PermissionDenied("You don't have permission to view this SOAP note.")

        is_doctor = request.user == appointment.doctor
        form = SOAPNoteEditForm(instance=soap_note) if is_doctor else None

        return render(request, 'transcription/soap_note_detail.html', {
            'soap_note': soap_note,
            'appointment': appointment,
            'is_doctor': is_doctor,
            'form': form,
        })


class SOAPNoteEditView(LoginRequiredMixin, View):
    def post(self, request, pk):
        soap_note = get_object_or_404(SOAPNote, pk=pk)
        appointment = soap_note.appointment

        if request.user != appointment.doctor:
            raise PermissionDenied("Only the doctor can edit SOAP notes.")

        form = SOAPNoteEditForm(request.POST, instance=soap_note)
        if form.is_valid():
            soap_note = form.save(commit=False)
            soap_note.is_edited = True
            soap_note.save()
            messages.success(request, "SOAP note updated successfully.")
            return redirect('soap_note_detail', pk=soap_note.pk)

        return render(request, 'transcription/soap_note_detail.html', {
            'soap_note': soap_note,
            'appointment': appointment,
            'is_doctor': True,
            'form': form,
        })


class SOAPNoteRegenerateView(LoginRequiredMixin, View):
    def post(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, pk=appointment_id)

        if request.user != appointment.doctor:
            raise PermissionDenied("Only the doctor can regenerate SOAP notes.")

        try:
            transcription = appointment.transcription
        except Transcription.DoesNotExist:
            messages.error(request, "No transcription found for this appointment.")
            return redirect('appointment_detail', pk=appointment.pk)

        if transcription.status != Transcription.Status.COMPLETED:
            messages.error(request, "Transcription is not completed yet.")
            return redirect('appointment_detail', pk=appointment.pk)

        # Delete existing SOAP note if any
        SOAPNote.objects.filter(appointment=appointment).delete()

        # Regenerate in background
        from .soap_service import SOAPNoteService
        SOAPNoteService.generate_in_background(transcription)

        messages.success(request, "SOAP note regeneration started. Please refresh in a few moments.")
        return redirect('appointment_detail', pk=appointment.pk)

import logging
import threading
import requests
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Transcription
from chikitsa360 import settings

logger = logging.getLogger(__name__)

# Groq's OpenAI-compatible Whisper endpoint.
GROQ_TRANSCRIBE_URL = "https://api.groq.com/openai/v1/audio/transcriptions"


class TranscriptionService:
    """Audio transcription via Groq's Whisper-large-v3 endpoint."""

    @staticmethod
    def _claim(transcription_id):
        """
        Atomically claim the transcription for processing.
        Returns True if PENDING|FAILED -> PROCESSING flip succeeded for this caller.
        """
        claimable = [Transcription.Status.PENDING, Transcription.Status.FAILED]
        rows = Transcription.objects.filter(
            id=transcription_id, status__in=claimable,
        ).update(
            status=Transcription.Status.PROCESSING,
            error_message=None,
        )
        return rows == 1

    @staticmethod
    def _whisper_call(audio_data, filename):
        """
        Send a single audio blob to Groq Whisper and return its verbose_json response.
        Raises on non-200.
        """
        api_key = settings.GROQ_API_KEY
        if not api_key:
            raise ValueError("GROQ_API_KEY not configured")

        files = {"file": (filename, audio_data, "audio/webm")}
        data = {
            "model": "whisper-large-v3",
            "response_format": "verbose_json",
            "language": "en",
            "temperature": "0.0",
        }
        headers = {"Authorization": f"Bearer {api_key}"}

        logger.info("Whisper request: file=%s size=%d", filename, len(audio_data))
        response = requests.post(
            GROQ_TRANSCRIBE_URL,
            headers=headers,
            files=files,
            data=data,
            timeout=180,
        )
        if response.status_code != 200:
            raise Exception(
                f"Groq Whisper error {response.status_code}: {response.text[:300]}"
            )
        return response.json()

    @staticmethod
    def _label_for(role):
        """role is 'doctor' or 'patient' (or anything else → speaker)."""
        if role == 'doctor':  return 'Doctor'
        if role == 'patient': return 'Patient'
        return 'Speaker'

    @staticmethod
    def _segments_with_label(whisper_result, label):
        """
        Pull segments out of Whisper's verbose_json. Returns a list of
        {'start': float, 'text': str, 'label': str}.
        Falls back to a single full-text segment if no segments are present.
        """
        segments = whisper_result.get('segments') or []
        out = []
        for seg in segments:
            text = (seg.get('text') or '').strip()
            if not text:
                continue
            out.append({
                'start': float(seg.get('start', 0) or 0),
                'text':  text,
                'label': label,
            })
        if not out:
            full = (whisper_result.get('text') or '').strip()
            if full:
                out.append({'start': 0.0, 'text': full, 'label': label})
        return out

    @staticmethod
    def _merge_transcripts(*segment_lists):
        """
        Merge segment lists from multiple speakers into a single chronologically
        ordered transcript. Adjacent segments from the same speaker are joined.
        """
        all_segments = [s for lst in segment_lists for s in lst]
        all_segments.sort(key=lambda s: s['start'])

        if not all_segments:
            return ''

        lines = []
        current_label = None
        current_text = []
        for seg in all_segments:
            if seg['label'] != current_label:
                if current_label is not None:
                    lines.append(f"{current_label}: {' '.join(current_text).strip()}")
                current_label = seg['label']
                current_text = [seg['text']]
            else:
                current_text.append(seg['text'])
        lines.append(f"{current_label}: {' '.join(current_text).strip()}")
        return '\n\n'.join(lines)

    @staticmethod
    def process_dual_audio(local_audio, remote_audio, transcription, local_role):
        """
        Transcribe local + remote audio separately, then merge by timestamp
        with speaker labels. Either side may be None / empty.

        local_role is 'doctor' or 'patient' — the side whose mic was 'local_audio'.
        Idempotent: returns existing transcript if already claimed.
        """
        if not TranscriptionService._claim(transcription.id):
            transcription.refresh_from_db()
            logger.info(
                "Transcription %s already claimed (status=%s) — skipping duplicate",
                transcription.id, transcription.status,
            )
            return transcription.content or ''

        transcription.refresh_from_db()

        try:
            local_label  = TranscriptionService._label_for(local_role)
            remote_label = TranscriptionService._label_for(
                'patient' if local_role == 'doctor' else 'doctor'
            )

            local_segments = []
            remote_segments = []
            duration = 0.0

            if local_audio:
                result = TranscriptionService._whisper_call(local_audio, 'local.webm')
                local_segments = TranscriptionService._segments_with_label(result, local_label)
                duration = max(duration, float(result.get('duration', 0) or 0))

            if remote_audio:
                result = TranscriptionService._whisper_call(remote_audio, 'remote.webm')
                remote_segments = TranscriptionService._segments_with_label(result, remote_label)
                duration = max(duration, float(result.get('duration', 0) or 0))

            transcript = TranscriptionService._merge_transcripts(local_segments, remote_segments)

            transcription.content = transcript
            transcription.audio_duration = duration
            transcription.status = Transcription.Status.COMPLETED
            transcription.save()

            no_audio = not transcript
            print(
                f"[TRANSCRIPTION] done id={transcription.id} "
                f"local_segs={len(local_segments)} remote_segs={len(remote_segments)} "
                f"chars={len(transcript)} no_audio={no_audio}"
            )

            threading.Thread(
                target=TranscriptionService.send_transcription_emails,
                args=(transcription,),
                kwargs={'no_audio': no_audio},
                daemon=True,
            ).start()

            if transcript:
                from .soap_service import SOAPNoteService
                SOAPNoteService.generate_in_background(transcription)

            return transcript

        except Exception as e:
            logger.exception("Transcription processing failed for %s", transcription.id)
            transcription.status = Transcription.Status.FAILED
            transcription.error_message = str(e)[:500]
            transcription.save()
            raise

    @staticmethod
    def process_audio(audio_data, transcription):
        """
        Single-track fallback (legacy). Treats the blob as a generic mixed
        recording and labels it 'Speaker'. Prefer process_dual_audio.
        """
        return TranscriptionService.process_dual_audio(
            local_audio=audio_data,
            remote_audio=None,
            transcription=transcription,
            local_role='unknown',
        )

    @staticmethod
    def send_transcription_emails(transcription, no_audio=False):
        """Send transcript / no-audio emails. Safe to call from a background thread."""
        try:
            appointment = transcription.appointment
            patient = appointment.patient
            doctor = appointment.doctor

            patient_label = patient.get_full_name() or patient.email
            doctor_label = doctor.get_full_name() or doctor.email

            print(f"[EMAIL] preparing transcription emails (no_audio={no_audio}) for appointment {appointment.id}")

            duration_seconds = int(transcription.audio_duration or 0)
            duration_str = f"{duration_seconds // 60} minutes, {duration_seconds % 60} seconds"

            context = {
                'patient_name': patient_label,
                'doctor_name': doctor_label,
                'appointment_date': appointment.appointment_date,
                'appointment_time': appointment.appointment_time,
                'transcription': transcription.content,
                'duration': duration_str,
                'no_audio': no_audio,
            }

            from_addr = settings.EMAIL_HOST_USER or 'noreply@healthmeter.local'

            if no_audio:
                patient_subject = f"Audio not captured — your consultation with Dr. {doctor_label} on {appointment.appointment_date}"
                doctor_subject = f"Audio not captured — consultation with {patient_label} on {appointment.appointment_date}"
            else:
                patient_subject = f"Your consultation transcript with Dr. {doctor_label} — {appointment.appointment_date}"
                doctor_subject = f"Consultation transcript with {patient_label} — {appointment.appointment_date}"

            patient_body = render_to_string('transcription/email_patient.html', context)
            patient_email = EmailMessage(
                subject=patient_subject,
                body=patient_body,
                from_email=from_addr,
                to=[patient.email],
            )
            patient_email.content_subtype = 'html'
            patient_email.send(fail_silently=False)
            print(f"[EMAIL] patient email sent to {patient.email}")

            doctor_body = render_to_string('transcription/email_doctor.html', context)
            doctor_email = EmailMessage(
                subject=doctor_subject,
                body=doctor_body,
                from_email=from_addr,
                to=[doctor.email],
            )
            doctor_email.content_subtype = 'html'
            doctor_email.send(fail_silently=False)
            print(f"[EMAIL] doctor email sent to {doctor.email}")

            print("[EMAIL] all transcription emails sent successfully")
        except Exception as e:
            print(f"[EMAIL] ERROR sending transcription emails: {e}")
            logger.error("Failed to send transcription emails for %s: %s",
                         getattr(transcription, 'id', None), e)
        finally:
            from django.db import connection
            connection.close()

import os
import requests
import logging
import threading
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from .models import Transcription
from chikitsa360 import settings

logger = logging.getLogger(__name__)


class TranscriptionService:
    """Service for handling transcription requests and processing."""

    @staticmethod
    def _claim(transcription_id):
        """
        Atomically claim the transcription for processing.

        Returns True if this caller successfully flipped status PENDING -> PROCESSING.
        Returns False if another worker already claimed it (concurrent submit) or
        the row is already past PENDING (FAILED gets retried; COMPLETED is skipped).
        """
        # Allow retry of FAILED rows: also include FAILED in the claim window.
        claimable_statuses = [
            Transcription.Status.PENDING,
            Transcription.Status.FAILED,
        ]
        rows = Transcription.objects.filter(
            id=transcription_id,
            status__in=claimable_statuses,
        ).update(
            status=Transcription.Status.PROCESSING,
            error_message=None,
        )
        return rows == 1

    @staticmethod
    def process_audio(audio_data, transcription):
        """
        Process audio with Deepgram. Idempotent under concurrent submissions.

        Returns the transcript string (may be empty if audio captured no speech).
        Raises on Deepgram failure; caller should mark FAILED.
        """
        # Atomic claim — second concurrent submitter exits cleanly here.
        if not TranscriptionService._claim(transcription.id):
            transcription.refresh_from_db()
            logger.info(
                "Transcription %s already claimed (status=%s) — skipping duplicate work",
                transcription.id, transcription.status,
            )
            return transcription.content or ''

        # Refresh in case _claim updated fields
        transcription.refresh_from_db()

        try:
            api_key = settings.DEEPGRAM_API_KEY
            if not api_key:
                raise ValueError("Deepgram API key not configured")

            # Save audio to a tmp file and stream it to Deepgram
            temp_file_path = f"/tmp/audio_{transcription.id}.webm"
            with open(temp_file_path, "wb") as f:
                f.write(audio_data)

            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "audio/webm",
            }

            # Deepgram params — model is env-overridable
            # Defaults: nova-3 (latest, best general English incl. Indian English)
            # Try "nova-2-medical" if you want clinical-domain tuning (English-only).
            model = os.environ.get('DEEPGRAM_MODEL', 'nova-3')
            params = {
                "model": model,
                "smart_format": "true",   # better numbers/dates/dosages
                "diarize": "true",         # speaker labels (DR vs PT)
                "punctuate": "true",
                "paragraphs": "true",      # cleaner formatting
                "utterances": "true",
                "detect_language": "true", # let Deepgram detect (Hindi/Hinglish/English)
            }

            logger.info("Sending audio to Deepgram (model=%s, size=%d bytes)",
                        model, len(audio_data))

            with open(temp_file_path, "rb") as audio_file:
                response = requests.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    data=audio_file,
                    timeout=120,
                )

            try:
                os.remove(temp_file_path)
            except OSError:
                pass

            if response.status_code != 200:
                error_msg = f"Deepgram API error: {response.status_code} - {response.text[:300]}"
                logger.error(error_msg)
                raise Exception(error_msg)

            result = response.json()
            transcript = TranscriptionService._extract_transcript(result)
            duration = result.get('metadata', {}).get('duration', 0)

            transcription.content = transcript or ''
            transcription.audio_duration = duration
            transcription.status = Transcription.Status.COMPLETED
            transcription.save()

            # Always notify both parties — even if empty (so they're not in the dark).
            no_audio = not transcript
            print(f"[TRANSCRIPTION] done id={transcription.id} chars={len(transcript)} no_audio={no_audio}")

            threading.Thread(
                target=TranscriptionService.send_transcription_emails,
                args=(transcription,),
                kwargs={'no_audio': no_audio},
                daemon=True,
            ).start()

            # SOAP only when we actually have speech to summarize
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
    def _extract_transcript(deepgram_result):
        """
        Pull the most useful transcript representation out of a Deepgram response.

        Prefers the diarized + paragraph-formatted text when available
        (gives "Speaker 0: ...\\n\\nSpeaker 1: ..." which the SOAP LLM can attribute).
        Falls back to the flat alternative.transcript for older responses.
        """
        try:
            channels = deepgram_result.get('results', {}).get('channels', [])
            if not channels:
                return ''
            alt = channels[0].get('alternatives', [{}])[0]

            paragraphs_text = (
                alt.get('paragraphs', {}).get('transcript')
                if isinstance(alt.get('paragraphs'), dict)
                else None
            )
            if paragraphs_text:
                return paragraphs_text.strip()

            return (alt.get('transcript') or '').strip()
        except (KeyError, IndexError, AttributeError, TypeError):
            return ''

    @staticmethod
    def send_transcription_emails(transcription, no_audio=False):
        """
        Send transcription emails to both doctor and patient.
        Safe to call from a background thread.

        no_audio=True sends a "we couldn't capture audio" notification instead.
        """
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

            # Patient
            if no_audio:
                patient_subject = f"Audio not captured — your consultation with Dr. {doctor_label} on {appointment.appointment_date}"
            else:
                patient_subject = f"Your consultation transcript with Dr. {doctor_label} — {appointment.appointment_date}"

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

            # Doctor
            if no_audio:
                doctor_subject = f"Audio not captured — consultation with {patient_label} on {appointment.appointment_date}"
            else:
                doctor_subject = f"Consultation transcript with {patient_label} — {appointment.appointment_date}"

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

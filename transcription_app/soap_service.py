import json
import logging
import threading
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"

SOAP_SYSTEM_PROMPT = """You are a medical documentation assistant. Given a consultation transcription between a doctor and patient, generate structured SOAP notes.

Return your response as a JSON object with exactly these 4 keys:
- "subjective": Patient's reported symptoms, history, complaints, and concerns as discussed in the conversation
- "objective": Observable clinical findings, vital signs, physical examination findings mentioned
- "assessment": Clinical assessment, diagnosis or differential diagnoses discussed
- "plan": Treatment plan, medications prescribed, follow-up instructions, referrals

If information for a section is not available in the transcription, write "Not discussed during this consultation."

Return ONLY the JSON object."""


class SOAPNoteService:
    @staticmethod
    def generate_soap_notes(transcription):
        """Generate SOAP notes from a transcription. Meant to run in a background thread."""
        from .models import SOAPNote

        soap_note = None
        try:
            soap_note, created = SOAPNote.objects.get_or_create(
                appointment=transcription.appointment,
                transcription=transcription,
                defaults={'status': SOAPNote.Status.PENDING},
            )

            if not created and soap_note.status == SOAPNote.Status.COMPLETED:
                logger.info("SOAP note already completed, skipping generation")
                return

            soap_note.status = SOAPNote.Status.GENERATING
            soap_note.save()

            if not transcription.content or not transcription.content.strip():
                soap_note.status = SOAPNote.Status.FAILED
                soap_note.error_message = "Transcription content is empty"
                soap_note.save()
                return

            api_key = settings.GROQ_API_KEY
            if not api_key:
                raise ValueError("GROQ_API_KEY not configured")

            model = settings.GROQ_MODEL or 'openai/gpt-oss-120b'

            body = {
                "model": model,
                "messages": [
                    {"role": "system", "content": SOAP_SYSTEM_PROMPT},
                    {"role": "user",
                     "content": f"Consultation Transcription:\n\n{transcription.content}"},
                ],
                "temperature": 0.3,
                "max_tokens": 2000,
                # Force valid JSON output — no markdown stripping needed.
                "response_format": {"type": "json_object"},
            }
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            }

            logger.info("Calling Groq chat for SOAP (model=%s, transcript=%d chars)",
                        model, len(transcription.content))

            response = requests.post(
                GROQ_CHAT_URL,
                headers=headers,
                json=body,
                timeout=60,
            )

            if response.status_code != 200:
                raise Exception(
                    f"Groq chat error {response.status_code}: {response.text[:300]}"
                )

            payload = response.json()
            content = payload["choices"][0]["message"]["content"]
            data = json.loads(content)

            soap_note.subjective = data.get("subjective", "") or ""
            soap_note.objective = data.get("objective", "") or ""
            soap_note.assessment = data.get("assessment", "") or ""
            soap_note.plan = data.get("plan", "") or ""
            soap_note.status = SOAPNote.Status.COMPLETED
            soap_note.error_message = None
            soap_note.save()

            logger.info("SOAP note generated for appointment %s",
                        transcription.appointment.id)

        except json.JSONDecodeError as e:
            logger.error("Failed to parse SOAP JSON: %s", e)
            if soap_note is not None:
                try:
                    soap_note.status = SOAPNote.Status.FAILED
                    soap_note.error_message = f"Failed to parse AI response: {e}"
                    soap_note.save()
                except Exception:
                    pass
        except Exception as e:
            logger.exception("SOAP note generation failed")
            if soap_note is not None:
                try:
                    soap_note.status = SOAPNote.Status.FAILED
                    soap_note.error_message = str(e)[:500]
                    soap_note.save()
                except Exception:
                    pass
        finally:
            from django.db import connection
            connection.close()

    @staticmethod
    def generate_in_background(transcription):
        """Launch SOAP note generation in a background thread."""
        thread = threading.Thread(
            target=SOAPNoteService.generate_soap_notes,
            args=(transcription,),
            daemon=True,
        )
        thread.start()
        return thread

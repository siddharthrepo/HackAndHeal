import json
import logging
import threading
from django.conf import settings

logger = logging.getLogger(__name__)

SOAP_SYSTEM_PROMPT = """You are a medical documentation assistant. Given a consultation transcription between a doctor and patient, generate structured SOAP notes.

Return your response as a JSON object with exactly these 4 keys:
- "subjective": Patient's reported symptoms, history, complaints, and concerns as discussed in the conversation
- "objective": Observable clinical findings, vital signs, physical examination findings mentioned
- "assessment": Clinical assessment, diagnosis or differential diagnoses discussed
- "plan": Treatment plan, medications prescribed, follow-up instructions, referrals

If information for a section is not available in the transcription, write "Not discussed during this consultation."

IMPORTANT: Return ONLY the JSON object, no markdown formatting, no code blocks, no extra text."""


class SOAPNoteService:
    @staticmethod
    def generate_soap_notes(transcription):
        """Generate SOAP notes from a transcription using Groq LLM. Meant to run in a background thread."""
        from .models import SOAPNote
        try:
            soap_note, created = SOAPNote.objects.get_or_create(
                appointment=transcription.appointment,
                transcription=transcription,
                defaults={'status': SOAPNote.Status.PENDING}
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

            from langchain_groq import ChatGroq
            from langchain_core.messages import SystemMessage, HumanMessage

            llm = ChatGroq(
                api_key=settings.GROQ_API_KEY,
                model=settings.GROQ_MODEL,
                temperature=0.3,
                max_tokens=2000,
            )

            messages = [
                SystemMessage(content=SOAP_SYSTEM_PROMPT),
                HumanMessage(content=f"Consultation Transcription:\n\n{transcription.content}"),
            ]

            response = llm.invoke(messages)
            raw_text = response.content.strip()

            # Handle markdown code block wrapping
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                # Remove first and last lines (```json and ```)
                lines = [l for l in lines if not l.strip().startswith("```")]
                raw_text = "\n".join(lines)

            data = json.loads(raw_text)

            soap_note.subjective = data.get("subjective", "")
            soap_note.objective = data.get("objective", "")
            soap_note.assessment = data.get("assessment", "")
            soap_note.plan = data.get("plan", "")
            soap_note.status = SOAPNote.Status.COMPLETED
            soap_note.error_message = None
            soap_note.save()

            logger.info(f"SOAP note generated successfully for appointment {transcription.appointment.id}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse SOAP note JSON: {e}")
            try:
                soap_note.status = SOAPNote.Status.FAILED
                soap_note.error_message = f"Failed to parse AI response: {e}"
                soap_note.save()
            except Exception:
                pass
        except Exception as e:
            logger.exception("SOAP note generation failed")
            try:
                soap_note.status = SOAPNote.Status.FAILED
                soap_note.error_message = str(e)
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

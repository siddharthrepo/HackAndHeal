import os
import requests
import json
import base64
import time
import logging
# from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Transcription
from chikitsa360 import settings

# Set up logging
logger = logging.getLogger(__name__)

class TranscriptionService:
    """
    Service for handling transcription requests and processing.
    """
    @staticmethod
    def process_audio(audio_data, transcription):
        """
        Process audio data and generate transcription using Deepgram API.
        """
        try:
            transcription.status = Transcription.Status.PROCESSING
            transcription.save()
            
            # Get Deepgram API key with error handling
            
            api_key =  settings.DEEPGRAM_API_KEY

            if not api_key:
                logger.error("Deepgram API key is missing in settings")
                raise ValueError("Deepgram API key not configured properly")
            
            # For debugging purposes
            logger.info(f"API Key length: {len(api_key)}")
            
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            
            # Save the audio data to a temporary file
            temp_file_path = f"/tmp/audio_{transcription.id}.webm"
            with open(temp_file_path, "wb") as f:
                f.write(audio_data)
            
            # Create the proper payload format for Deepgram
            # They require either a "url" or a binary upload, not base64 in JSON
            # Let's use the audio_url approach
            with open(temp_file_path, "rb") as audio_file:
                # Directly send the binary data rather than as JSON
                headers = {
                    "Authorization": f"Token {api_key}",
                    "Content-Type": "audio/webm"  # Set the content type to match the audio format
                }
                
                # Query parameters for Deepgram
                params = {
                    "model": "general",
                    "language": "en-US",
                    "detect_language": "true",
                    "punctuate": "true",
                    "utterances": "true"
                }
                
                logger.info("Sending request to Deepgram API")
                response = requests.post(
                    "https://api.deepgram.com/v1/listen",
                    headers=headers,
                    params=params,
                    data=audio_file  # Send the file as binary data
                )
            
            # Clean up the temporary file
            # if os.path.exists(temp_file_path):
            #     os.remove(temp_file_path)
            
            # Log the response for debugging
            logger.debug(f"Deepgram API response status: {response.status_code}")
            logger.debug(f"Deepgram API response content: {response.text[:200]}...")  # Log first 200 chars
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract transcript from the response
                transcript = result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
                
                if not transcript:
                    logger.warning("No transcript found in the response")
                    # raise Exception("No transcript found in the response")
                    transcript = "nothing here"
                
                # Update transcription
                transcription.content = transcript
                transcription.status = Transcription.Status.COMPLETED
                transcription.audio_duration = result.get('metadata', {}).get('duration', 0)
                transcription.save()
                
                # Send emails with the transcription
                print(transcription.content)
                TranscriptionService.send_transcription_emails(transcription)
                
                return transcript
            else:
                error_msg = f"Deepgram API error: {response.status_code} - {response.text}"
                logger.error(error_msg)
                raise Exception(error_msg)
                
        except Exception as e:
            logger.exception("Transcription processing failed")
            transcription.status = Transcription.Status.FAILED
            transcription.error_message = str(e)
            transcription.save()
            raise
    
    
    @staticmethod
    def send_transcription_emails(transcription):
        """
        Send transcription emails to both doctor and patient.
        """
        appointment = transcription.appointment
        patient = appointment.patient
        doctor = appointment.doctor
        
        # Prepare email context
        context = {
            'patient_name': patient.get_full_name() or patient.email,
            'doctor_name': doctor.get_full_name() or doctor.email,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'transcription': transcription.content,
            'duration': f"{int(transcription.audio_duration // 60)} minutes, {int(transcription.audio_duration % 60)} seconds"
        }
        
        # Send email to patient
        patient_subject = f"Your consultation transcript with Dr. {doctor.last_name} - {appointment.appointment_date}"
        patient_html_message = render_to_string('transcription/email_patient.html', context)
        patient_email = EmailMessage(
            subject=patient_subject,
            body=patient_html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[patient.email]
        )
        patient_email.content_subtype = 'html'
        patient_email.send()
        
        # Send email to doctor
        doctor_subject = f"Consultation transcript with {patient.last_name} - {appointment.appointment_date}"
        doctor_html_message = render_to_string('transcription/email_doctor.html', context)
        doctor_email = EmailMessage(
            subject=doctor_subject,
            body=doctor_html_message,
            from_email=settings.EMAIL_HOST_USER,
            to=[doctor.email]
        )
        doctor_email.content_subtype = 'html'
        doctor_email.send()

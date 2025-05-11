import os
import requests
import json
import base64
import time
from django.conf import settings
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Transcription

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
            
            # Use Deepgram for transcription
            api_key = settings.DEEPGRAM_API_KEY
            
            headers = {
                "Authorization": f"Token {api_key}",
                "Content-Type": "application/json"
            }
            
            # Base64 encode the audio data
            encoded_audio = base64.b64encode(audio_data).decode('utf-8')
            
            payload = {
                "audio_base64": encoded_audio,
                "model": "general",
                "language": "en-US",
                "detect_language": True,
                "punctuate": True,
                "utterances": True
            }
            
            response = requests.post(
                "https://api.deepgram.com/v1/listen",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Extract transcript from the response
                transcript = result.get('results', {}).get('channels', [{}])[0].get('alternatives', [{}])[0].get('transcript', '')
                
                if not transcript:
                    raise Exception("No transcript found in the response")
                
                # Update transcription
                transcription.content = transcript
                transcription.status = Transcription.Status.COMPLETED
                transcription.audio_duration = result.get('metadata', {}).get('duration', 0)
                transcription.save()
                
                # Send emails with the transcription
                TranscriptionService.send_transcription_emails(transcription)
                
                return transcript
            else:
                raise Exception(f"Deepgram API error: {response.text}")
        
        except Exception as e:
            transcription.status = Transcription.Status.FAILED
            transcription.error_message = str(e)
            transcription.save()
            raise
    
    @staticmethod
    def use_openai_whisper(audio_data, transcription):
        """
        Alternative method to process audio using OpenAI Whisper API.
        """
        try:
            transcription.status = Transcription.Status.PROCESSING
            transcription.save()
            
            import openai
            openai.api_key = settings.OPENAI_API_KEY
            
            # Save audio data to a temporary file
            temp_file_path = "/tmp/audio_temp.mp3"
            with open(temp_file_path, "wb") as f:
                f.write(audio_data)
            
            # Use OpenAI Whisper API
            with open(temp_file_path, "rb") as audio_file:
                response = openai.Audio.transcribe(
                    model="whisper-1",
                    file=audio_file,
                    language="en"
                )
            
            # Clean up temporary file
            os.remove(temp_file_path)
            
            # Extract transcript
            transcript = response.get('text', '')
            
            if not transcript:
                raise Exception("No transcript found in the response")
            
            # Update transcription
            transcription.content = transcript
            transcription.status = Transcription.Status.COMPLETED
            transcription.save()
            
            # Send emails with the transcription
            TranscriptionService.send_transcription_emails(transcription)
            
            return transcript
        
        except Exception as e:
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
            from_email=settings.DEFAULT_FROM_EMAIL,
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
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[doctor.email]
        )
        doctor_email.content_subtype = 'html'
        doctor_email.send()

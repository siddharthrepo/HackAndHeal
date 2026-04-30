# HealthMeter — Healthcare! Everywhere!

A comprehensive telehealth platform built with Django, enabling video consultations, real-time chat, AI-powered clinical documentation, and digital prescriptions.

## Features

### Core
- **Video Consultations** — Powered by Daily.co with real-time audio/video
- **Real-Time Chat** — Django Channels WebSocket messaging
- **Online Payments** — Razorpay integration for consultation fees
- **Role-Based Access** — Separate flows for patients, doctors, and admins

### AI-Powered SOAP Notes
- Automatic SOAP (Subjective/Objective/Assessment/Plan) note generation from consultation transcriptions
- Uses Groq LLM (LLaMA 3.3 70B) via LangChain
- Doctors can view, edit, and regenerate notes; patients get read-only access
- Generated in the background immediately after transcription completes

### Digital Prescription Generator
- Doctors create prescriptions with diagnosis, medications, dosage, and instructions
- Dynamic inline formset for adding/removing medication items
- Professional PDF generation using ReportLab with clinic branding
- Patients and doctors can download prescriptions as PDF

### Smart Appointment Reminders & Follow-Up
- Automated email reminders at 24 hours and 1 hour before appointments
- Follow-up date scheduling by doctors with patient email reminders
- Management command `send_reminders` for cron/scheduler integration
- Token-protected HTTP endpoint for external trigger (e.g., Koyeb cron)

### Transcription
- Audio recording via Web Audio API (mixes local + remote audio)
- Deepgram API for speech-to-text
- Email transcripts to both participants

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5, Django Channels |
| Database | PostgreSQL |
| Video | Daily.co (callObject mode) |
| Transcription | Deepgram API |
| AI/LLM | Groq (LLaMA 3.3 70B) via LangChain |
| PDF | ReportLab |
| Payments | Razorpay |
| Frontend | Tailwind CSS (CDN), vanilla JS |
| Deployment | Docker, Koyeb |

## Setup

```bash
# Clone & install
git clone <repo-url>
cd chikitsa360
pip install -r requirements.txt

# Configure .env (copy from .env.example and fill in values)
cp .env.example .env

# Database
python manage.py migrate

# Run
python manage.py runserver
```

### Environment Variables

| Variable | Description |
|----------|-------------|
| `SECRET_KEY` | Django secret key |
| `DEBUG` | `True` / `False` |
| `DATABASE_URL` | PostgreSQL connection string (production) |
| `DAILY_API_KEY` | Daily.co API key for video rooms |
| `DEEPGRAM_API_KEY` | Deepgram API key for transcription |
| `GROQ_API_KEY` | Groq API key for SOAP note generation |
| `GROQ_MODEL` | Groq model name (default: `llama-3.3-70b-versatile`) |
| `RAZORPAY_KEY_ID` | Razorpay key ID |
| `RAZORPAY_KEY_SECRET` | Razorpay key secret |
| `REMINDER_CRON_TOKEN` | Token for the reminder trigger endpoint |

### Running Reminders

Set up a cron job or external scheduler to call:

```bash
# Via management command
python manage.py send_reminders

# Or via HTTP endpoint
curl "https://your-domain.com/api/trigger-reminders/?token=YOUR_TOKEN"
```

## Project Structure

```
chikitsa360/
├── auth_app/          # User auth, profiles, roles
├── consultation_app/  # Appointments, availability, prescriptions, follow-ups, reminders
├── payment_app/       # Razorpay payment processing
├── chat_app/          # WebSocket real-time chat
├── transcription_app/ # Deepgram transcription, AI SOAP notes
├── templates/         # Django templates
├── static/            # CSS, JS, images
└── chikitsa360/       # Project settings & URLs
```

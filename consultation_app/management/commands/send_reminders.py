import logging
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.conf import settings
from consultation_app.models import Appointment, FollowUp

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send appointment reminders (24h, 1h) and follow-up reminders'

    def handle(self, *args, **options):
        now = timezone.now()
        sent_count = 0

        # ── 24-hour reminders ──
        window_start_24 = now + timedelta(hours=23, minutes=30)
        window_end_24 = now + timedelta(hours=24, minutes=30)

        appointments_24h = Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            reminder_24h_sent=False,
        )

        for appt in appointments_24h:
            appt_dt = timezone.make_aware(
                timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
            )
            if window_start_24 <= appt_dt <= window_end_24:
                self._send_reminder(appt, '24h')
                appt.reminder_24h_sent = True
                appt.save(update_fields=['reminder_24h_sent'])
                sent_count += 1

        # ── 1-hour reminders ──
        window_start_1 = now + timedelta(minutes=50)
        window_end_1 = now + timedelta(minutes=70)

        appointments_1h = Appointment.objects.filter(
            status=Appointment.Status.CONFIRMED,
            reminder_1h_sent=False,
        )

        for appt in appointments_1h:
            appt_dt = timezone.make_aware(
                timezone.datetime.combine(appt.appointment_date, appt.appointment_time)
            )
            if window_start_1 <= appt_dt <= window_end_1:
                self._send_reminder(appt, '1h')
                appt.reminder_1h_sent = True
                appt.save(update_fields=['reminder_1h_sent'])
                sent_count += 1

        # ── Follow-up reminders ──
        today = now.date()
        follow_ups = FollowUp.objects.filter(
            follow_up_date=today,
            reminder_sent=False,
        ).select_related('appointment', 'appointment__patient', 'appointment__doctor')

        for fu in follow_ups:
            self._send_followup_reminder(fu)
            fu.reminder_sent = True
            fu.save(update_fields=['reminder_sent'])
            sent_count += 1

        self.stdout.write(self.style.SUCCESS(f'Sent {sent_count} reminder(s).'))

    def _send_reminder(self, appointment, reminder_type):
        patient = appointment.patient
        doctor = appointment.doctor
        time_label = 'tomorrow' if reminder_type == '24h' else 'in 1 hour'

        context = {
            'patient_name': patient.get_full_name() or patient.email,
            'doctor_name': doctor.get_full_name() or doctor.email,
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'time_label': time_label,
        }

        # Patient email
        try:
            patient_html = render_to_string('reminders/reminder_patient.html', context)
            EmailMessage(
                subject=f"Reminder: Your appointment is {time_label}",
                body=patient_html,
                from_email=settings.EMAIL_HOST_USER,
                to=[patient.email],
            ).send()
        except Exception as e:
            logger.error(f"Failed to send patient reminder: {e}")

        # Doctor email
        try:
            doctor_html = render_to_string('reminders/reminder_doctor.html', context)
            EmailMessage(
                subject=f"Reminder: Appointment with {patient.get_full_name()} is {time_label}",
                body=doctor_html,
                from_email=settings.EMAIL_HOST_USER,
                to=[doctor.email],
            ).send()
        except Exception as e:
            logger.error(f"Failed to send doctor reminder: {e}")

    def _send_followup_reminder(self, follow_up):
        appointment = follow_up.appointment
        patient = appointment.patient
        doctor = appointment.doctor

        context = {
            'patient_name': patient.get_full_name() or patient.email,
            'doctor_name': doctor.get_full_name() or doctor.email,
            'follow_up_date': follow_up.follow_up_date,
            'notes': follow_up.notes,
            'original_date': appointment.appointment_date,
        }

        try:
            html = render_to_string('reminders/followup_patient.html', context)
            email = EmailMessage(
                subject=f"Follow-up Reminder: Schedule your visit with Dr. {doctor.last_name}",
                body=html,
                from_email=settings.EMAIL_HOST_USER,
                to=[patient.email],
            )
            email.content_subtype = 'html'
            email.send()
        except Exception as e:
            logger.error(f"Failed to send follow-up reminder: {e}")

from django.urls import path
from .views import (
    HomeView, DoctorSearchView, DoctorDetailView,
    AvailabilityCreateView, AvailabilityDeleteView, DoctorAvailabilityView,
    BookAppointmentView, AppointmentDetailView, JoinConsultationView,
    PatientAppointmentsView, DoctorAppointmentsView,
    UpdateAppointmentStatusView, CancelAppointmentView,
    PrescriptionCreateView, PrescriptionDetailView, PrescriptionPDFView,
    FollowUpCreateView, TriggerRemindersView,
)

urlpatterns = [
    # Public pages
    path('', HomeView.as_view(), name='home'),
    path('doctors/search/', DoctorSearchView.as_view(), name='doctor_search'),
    path('doctors/<int:pk>/', DoctorDetailView.as_view(), name='doctor_detail'),
    
    # Doctor availability management
    path('availability/create/', AvailabilityCreateView.as_view(), name='availability_create'),
    path('availability/<int:pk>/delete/', AvailabilityDeleteView.as_view(), name='availability_delete'),
    path('doctor/availability/', DoctorAvailabilityView.as_view(), name='doctor_availability'),
    
    # Appointment management
    path('appointment/book/<int:availability_id>/', BookAppointmentView.as_view(), name='book_appointment'),
    path('appointment/<uuid:pk>/', AppointmentDetailView.as_view(), name='appointment_detail'),
    path('appointment/<uuid:pk>/join/', JoinConsultationView.as_view(), name='join_consultation'),
    path('patient/appointments/', PatientAppointmentsView.as_view(), name='patient_appointments'),
    path('doctor/appointments/', DoctorAppointmentsView.as_view(), name='doctor_appointments'),
    path('appointment/<uuid:pk>/update-status/', UpdateAppointmentStatusView.as_view(), name='update_appointment_status'),
    path('appointment/<uuid:pk>/cancel/', CancelAppointmentView.as_view(), name='cancel_appointment'),
    # Video call
    # consultation_app/urls.py or your main urls.py
    path('consultation/join/<uuid:pk>/', JoinConsultationView.as_view(), name='join_video_call'),

    # Prescriptions
    path('appointment/<uuid:appointment_id>/prescription/create/', PrescriptionCreateView.as_view(), name='prescription_create'),
    path('prescription/<uuid:pk>/', PrescriptionDetailView.as_view(), name='prescription_detail'),
    path('prescription/<uuid:pk>/pdf/', PrescriptionPDFView.as_view(), name='prescription_pdf'),

    # Follow-up
    path('appointment/<uuid:appointment_id>/follow-up/', FollowUpCreateView.as_view(), name='follow_up_create'),

    # Reminders API
    path('api/trigger-reminders/', TriggerRemindersView.as_view(), name='trigger_reminders'),
]

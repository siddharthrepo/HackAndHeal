import json
import uuid
import requests
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, 
    DeleteView, TemplateView, FormView, View
)
from django.urls import reverse_lazy, reverse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse, HttpResponseRedirect, Http404
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from django.conf import settings
from django.core.exceptions import PermissionDenied
from auth_app.models import User, DoctorProfile
from auth_app.mixins import PatientRequiredMixin, DoctorRequiredMixin
from .models import Availability, Appointment, Service, Testimonial, HealthTip
from .forms import AvailabilityForm, AppointmentForm, DoctorSearchForm
from payment_app.models import Payment

class HomeView(TemplateView):
    """
    Landing page with doctor search functionality.
    """
    template_name = 'index.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DoctorSearchForm()
        
        # Get featured doctors (for example, those with most appointments)
        doctor_users = User.objects.filter(role=User.Role.DOCTOR, is_active=True)
        featured_doctors = []
        
        for doctor_user in doctor_users[:6]:  # Limit to 6 featured doctors
            try:
                doctor_profile = doctor_user.doctor_profile
                featured_doctors.append({
                    'user': doctor_user,
                    'profile': doctor_profile
                })
            except DoctorProfile.DoesNotExist:
                continue
        
        context['featured_doctors'] = featured_doctors
        
        # Get active services
        context['services'] = Service.objects.filter(is_active=True).order_by('display_order')[:8]
        
        # Get approved testimonials
        context['testimonials'] = Testimonial.objects.filter(is_approved=True).order_by('-is_featured', '-created_at')[:6]
        
        # Get featured health tips
        context['health_tips'] = HealthTip.objects.filter(is_featured=True).order_by('-created_at')[:3]
        
        context['fallback_tips'] = [
            {
                'icon': 'fa-tint',
                'title': 'Staying Hydrated: Why Water Matters',
                'content': 'Drinking adequate water is essential for maintaining good health...',
                'author': 'Dr. Amrita Singh',
                'date': 'May 5, 2025'
            },
            {
                'icon': 'fa-brain',
                'title': 'Managing Stress in Daily Life',
                'content': 'Chronic stress can affect your physical and mental health...',
                'author': 'Dr. Rahul Verma',
                'date': 'April 28, 2025'
            },
            {
                'icon': 'fa-running',
                'title': 'The Importance of Regular Exercise',
                'content': 'Regular physical activity improves cardiovascular health...',
                'author': 'Dr. Sanjay Mehta',
                'date': 'April 15, 2025'
            }
        ]

        
        return context

class DoctorSearchView(ListView):
    """
    View for searching doctors by name, specialty, or available dates.
    """
    model = User
    template_name = 'doctor_search_results.html'
    context_object_name = 'doctors'
    paginate_by = 10
    
    def get_queryset(self):
        form = DoctorSearchForm(self.request.GET)
        queryset = User.objects.filter(role=User.Role.DOCTOR, is_active=True)
        
        if form.is_valid():
            query = form.cleaned_data.get('query')
            specialty = form.cleaned_data.get('specialty')
            date = form.cleaned_data.get('date')
            
            if query:
                queryset = queryset.filter(
                    Q(first_name__icontains=query) | 
                    Q(last_name__icontains=query) |
                    Q(doctor_profile__specialty__icontains=query)
                )
            
            if specialty:
                queryset = queryset.filter(doctor_profile__specialty__icontains=specialty)
            
            if date:
                # Filter doctors with availabilities on the specified date
                queryset = queryset.filter(
                    availabilities__date=date,
                    availabilities__is_booked=False
                ).distinct()
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = DoctorSearchForm(self.request.GET)
        context['specialties'] = (
            User.objects
            .filter(role=User.Role.DOCTOR, is_active=True)
            .values_list('doctor_profile__specialty', flat=True)
            .distinct()
            .order_by('doctor_profile__specialty')
        )

        
        # Add doctor profiles to the context
        doctors_with_profiles = []
        for doctor in context['doctors']:
            try:
                profile = doctor.doctor_profile
                doctors_with_profiles.append({
                    'user': doctor,
                    'profile': profile
                })
            except DoctorProfile.DoesNotExist:
                continue
        
        context['doctors_with_profiles'] = doctors_with_profiles
        return context

class DoctorDetailView(DetailView):
    """
    Public view of a doctor's profile and availability.
    """
    model = User
    template_name = 'doctor/doctor_detail.html'
    context_object_name = 'doctor'
    
    def get_object(self, queryset=None):
        user = get_object_or_404(User, pk=self.kwargs.get('pk'), role=User.Role.DOCTOR, is_active=True)
        return user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get doctor profile
        try:
            context['profile'] = self.object.doctor_profile
        except DoctorProfile.DoesNotExist:
            context['profile'] = None
        
        # Get available slots for next 7 days
        today = timezone.now().date()
        seven_days_later = today + timedelta(days=7)
        
        available_slots = Availability.objects.filter(
            doctor=self.object,
            date__gte=today,
            date__lte=seven_days_later,
            is_booked=False
        ).order_by('date', 'start_time')
        
        context['available_slots'] = available_slots
        context['can_book'] = self.request.user.is_authenticated and self.request.user.is_patient()
        
        return context

class AvailabilityCreateView(LoginRequiredMixin, DoctorRequiredMixin, CreateView):
    """
    View for doctors to create availability slots.
    """
    model = Availability
    form_class = AvailabilityForm
    template_name = 'consultation/availability_form.html'
    success_url = reverse_lazy('doctor_availability')
    
    def form_valid(self, form):
        form.instance.doctor = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        messages.success(self.request, "Availability slot created successfully!")
        return reverse_lazy('doctor_availability')

class AvailabilityDeleteView(LoginRequiredMixin, DoctorRequiredMixin, DeleteView):
    """
    View for doctors to delete availability slots.
    """
    model = Availability
    template_name = 'consultation/availability_confirm_delete.html'
    success_url = reverse_lazy('doctor_availability')
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        if obj.doctor != self.request.user:
            raise PermissionDenied("You don't have permission to delete this availability.")
        if obj.is_booked:
            raise PermissionDenied("Cannot delete a booked availability slot.")
        return obj
    
    def get_success_url(self):
        messages.success(self.request, "Availability slot deleted successfully!")
        return reverse_lazy('doctor_availability')

from django.views import View
from django.shortcuts import render, redirect
from django.contrib import messages

class DoctorAvailabilityView(LoginRequiredMixin, DoctorRequiredMixin, View):
    def get(self, request):
        form = AvailabilityForm()
        availabilities = Availability.objects.filter(doctor=request.user).order_by('date', 'start_time')

        # Group by date
        availabilities_by_date = {}
        for availability in availabilities:
            date_str = availability.date.strftime('%Y-%m-%d')
            availabilities_by_date.setdefault(date_str, []).append(availability)

        return render(request, 'consultation/doctor_availability.html', {
            'form': form,
            'availabilities_by_date': availabilities_by_date
        })

    def post(self, request):
        form = AvailabilityForm(request.POST)
        if form.is_valid():
            new_slot = form.save(commit=False)
            new_slot.doctor = request.user
            new_slot.save()
            messages.success(request, "Availability slot added successfully.")
            return redirect('doctor_availability')  # replace with your actual URL name
        else:
            availabilities = Availability.objects.filter(doctor=request.user).order_by('date', 'start_time')
            availabilities_by_date = {}
            for availability in availabilities:
                date_str = availability.date.strftime('%Y-%m-%d')
                availabilities_by_date.setdefault(date_str, []).append(availability)

            return render(request, 'consultation/doctor_availability.html', {
                'form': form,
                'availabilities_by_date': availabilities_by_date
            })


class BookAppointmentView(LoginRequiredMixin, PatientRequiredMixin, CreateView):
    """
    View for patients to book appointments.
    """
    model = Appointment
    form_class = AppointmentForm
    template_name = 'patient/book_appointment.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Get the availability object
        self.availability = get_object_or_404(
            Availability, 
            pk=self.kwargs.get('availability_id'),
            is_booked=False
        )
        
        # Check if the slot is already booked or in the past
        if self.availability.is_booked or self.availability.is_past:
            messages.error(request, "This slot is no longer available.")
            return redirect('doctor_detail', pk=self.availability.doctor.pk)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['availability'] = self.availability
        context['doctor'] = self.availability.doctor
        
        try:
            context['doctor_profile'] = self.availability.doctor.doctor_profile
        except DoctorProfile.DoesNotExist:
            context['doctor_profile'] = None
        
        return context
    
    def form_valid(self, form):
        # Create appointment (but don't save yet)
        form.instance.patient = self.request.user
        form.instance.doctor = self.availability.doctor
        form.instance.availability = self.availability
        form.instance.appointment_date = self.availability.date
        form.instance.appointment_time = self.availability.start_time
        form.instance.status = Appointment.Status.REQUESTED
        
        # Mark availability as booked
        self.availability.is_booked = True
        self.availability.save()
        
        # Save the appointment
        appointment = form.save()
        
        # Redirect to payment
        return HttpResponseRedirect(
            reverse('payment_checkout', kwargs={'appointment_id': appointment.id})
        )

class AppointmentDetailView(LoginRequiredMixin, DetailView):
    """
    View for showing appointment details.
    """
    model = Appointment
    template_name = 'consultation/appointment_detail.html'
    context_object_name = 'appointment'
    
    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        
        # Check if the user has permission to view this appointment
        if self.request.user != obj.patient and self.request.user != obj.doctor and not self.request.user.is_admin():
            raise PermissionDenied("You don't have permission to view this appointment.")
        
        return obj
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add doctor profile to context
        try:
            context['doctor_profile'] = self.object.doctor.doctor_profile
        except DoctorProfile.DoesNotExist:
            context['doctor_profile'] = None
        
        # Add payment details to context
        try:
            context['payment'] = Payment.objects.get(appointment=self.object)
        except Payment.DoesNotExist:
            context['payment'] = None
        
        context['is_doctor'] = self.request.user.is_doctor()
        context['is_patient'] = self.request.user.is_patient()
        return context

class JoinConsultationView(LoginRequiredMixin, View):
    def get(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        from django.conf import settings
        if request.user != appointment.patient and request.user != appointment.doctor:
            raise PermissionDenied("You don't have permission to join this consultation.")

        if appointment.status != Appointment.Status.CONFIRMED:
            messages.error(request, "This appointment is not confirmed.")
            return redirect('appointment_detail', pk=appointment.pk)

        if not appointment.can_join:
            messages.error(request, "It's not time for this appointment yet or it has already passed.")
            return redirect('appointment_detail', pk=appointment.pk)

        if not appointment.video_room_id:
            room_name = appointment.video_room_id
            try:
                room_name = f"chikitsa360-{uuid.uuid4().hex}"
                daily_api_key = settings.DAILY_API_KEY

                headers = {
                    'Authorization': f'Bearer {daily_api_key}',
                    'Content-Type': 'application/json'
                }

                data = {
                    'name': room_name,
                    'properties': {
                        'enable_chat': True,
                        'start_audio_off': False,
                        'start_video_off': False,
                        'exp': int((timezone.now() + timedelta(hours=2)).timestamp())
                    }
                }

                print("Sending request to create room...")
                response = requests.post('https://api.daily.co/v1/rooms', headers=headers, json=data)

                if response.status_code == 200:
                    room_data = response.json()
                    print(f"Room created successfully: {room_data}")
                    appointment.video_room_id = room_data['name']
                    appointment.save()
                else:
                    print(f"Failed to create room, status code: {response.status_code}")
                    messages.error(request, "Failed to create video room. Please try again.")
                    return redirect('appointment_detail', pk=appointment.pk)

            except Exception as e:
                print(f"An error occurred while creating room: {str(e)}")
                messages.error(request, f"An error occurred: {str(e)}")
                return redirect('appointment_detail', pk=appointment.pk)
            room_name = appointment.video_room_id
            print("room_name_0 -:", room_name)
        try:
            print(f"Generating access token for room: {appointment.video_room_id}")
            daily_api_key = settings.DAILY_API_KEY
            headers = {
                'Authorization': f'Bearer {daily_api_key}',
                'Content-Type': 'application/json'
            }

            data = {
                "properties": {
                    "start_audio_off": True,  
                    "start_video_off": True,  
                    "exp": int((timezone.now() + timedelta(hours=2)).timestamp()),  
                }
            }

            room_url = f'https://api.daily.co/v1/meeting-tokens'
            print("Sending request to generate token...")
            response = requests.post(room_url, headers=headers, json=data)

            if response.status_code == 200:
                token_data = response.json()
                token = token_data['token']
                print(f"Token generated: {token}")
            else:
                print(f"Failed to generate token, status code: {response.status_code}")
                messages.error(request, "Failed to generate access token. Please try again.")
                return redirect('appointment_detail', pk=appointment.pk)

        except Exception as e:
            print(f"An error occurred while generating token: {str(e)}")
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('appointment_detail', pk=appointment.pk)
        
        context = {
            'appointment': appointment,
            'room_name': appointment.video_room_id,
            'token': token,
            'is_doctor': request.user.is_doctor(),
            'patient_name': appointment.patient.get_full_name() or appointment.patient.email,
            'doctor_name': appointment.doctor.get_full_name() or appointment.doctor.email,
            'reason': appointment.reason
        }

        return render(request, 'consultation/video_room.html', context)

class PatientAppointmentsView(LoginRequiredMixin, PatientRequiredMixin, ListView):
    """
    View for patients to see their appointments.
    """
    model = Appointment
    template_name = 'patient/patient_appointments.html'
    context_object_name = 'appointments'
    
    def get_queryset(self):
        return Appointment.objects.filter(patient=self.request.user).order_by('-appointment_date', '-appointment_time')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Separate upcoming and past appointments
        today = timezone.now().date()
        
        upcoming_appointments = []
        past_appointments = []
        
        for appointment in context['appointments']:
            if appointment.appointment_date >= today:
                upcoming_appointments.append(appointment)
            else:
                past_appointments.append(appointment)
        
        context['upcoming_appointments'] = upcoming_appointments
        context['past_appointments'] = past_appointments
        
        return context

class DoctorAppointmentsView(LoginRequiredMixin, DoctorRequiredMixin, ListView):
    """
    View for doctors to see their appointments.
    """
    model = Appointment
    template_name = 'doctor/doctor_appointments.html'
    context_object_name = 'appointments'

    def get_queryset(self):
        return Appointment.objects.filter(doctor=self.request.user).order_by('-appointment_date', '-appointment_time')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        today = timezone.now().date()
        upcoming = []
        today_ = []
        past = []

        for appt in context['appointments']:
            if appt.appointment_date > today:
                upcoming.append(appt)
            elif appt.appointment_date == today:
                today_.append(appt)
            else:
                past.append(appt)

        context['appointment_sections'] = [
            {"label": "Today's Appointments", "appointments": today_},
            {"label": "Upcoming Appointments", "appointments": upcoming},
            {"label": "Past Appointments", "appointments": past},
        ]
        return context

class UpdateAppointmentStatusView(LoginRequiredMixin, DoctorRequiredMixin, View):
    """
    View for doctors to update appointment status.
    """
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Check if the user has permission
        if request.user != appointment.doctor:
            raise PermissionDenied("You don't have permission to update this appointment.")
        
        status = request.POST.get('status')
        if status in [choice[0] for choice in Appointment.Status.choices]:
            appointment.status = status
            appointment.save()
            messages.success(request, f"Appointment status updated to {appointment.get_status_display()}.")
        else:
            messages.error(request, "Invalid status provided.")
        
        return redirect('appointment_detail', pk=appointment.pk)

class CancelAppointmentView(LoginRequiredMixin, View):
    """
    View for patients and doctors to cancel appointments.
    """
    def post(self, request, pk):
        appointment = get_object_or_404(Appointment, pk=pk)
        
        # Check if the user has permission
        if request.user != appointment.patient and request.user != appointment.doctor:
            raise PermissionDenied("You don't have permission to cancel this appointment.")
        
        # Check if the appointment can be canceled
        if appointment.is_past:
            messages.error(request, "Cannot cancel a past appointment.")
            return redirect('appointment_detail', pk=appointment.pk)
        
        # Update appointment status
        appointment.status = Appointment.Status.CANCELLED
        appointment.save()
        
        # If the appointment has an availability, mark it as available again
        if appointment.availability:
            appointment.availability.is_booked = False
            appointment.availability.save()
        
        messages.success(request, "Appointment cancelled successfully.")
        
        # Redirect based on user role
        if request.user.is_patient():
            return redirect('patient_appointments')
        else:
            return redirect('doctor_appointments')

from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.contrib.auth import login, authenticate
from django.contrib.auth.views import LoginView, LogoutView
from django.views.generic import CreateView, UpdateView, DetailView, TemplateView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.http import HttpResponseRedirect
from .models import User, Profile, DoctorProfile
from .forms import UserRegistrationForm, ProfileForm, DoctorProfileForm, CustomAuthenticationForm, UserUpdateForm
from .mixins import PatientRequiredMixin, DoctorRequiredMixin, AdminRequiredMixin
from django.contrib.auth import login, get_backends
class CustomLoginView(LoginView):
    """Custom login view with our own template and form."""
    form_class = CustomAuthenticationForm
    template_name = 'auth/login.html'
    
    def get_success_url(self):
        """Redirect users based on their role."""
        user = self.request.user
        if user.is_admin():
            return reverse_lazy('admin_dashboard')
        elif user.is_doctor():
            return reverse_lazy('doctor_dashboard')
        else:
            return reverse_lazy('patient_dashboard')

class CustomLogoutView(LogoutView):
    """Custom logout view."""
    next_page = 'home'


class RegisterView(CreateView):
    """View for user registration."""
    model = User
    form_class = UserRegistrationForm
    template_name = 'auth/register.html'
    

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_active = True
        user.save()

        # Create a profile for the user
        Profile.objects.create(user=user)

        # If the user is a doctor, create a doctor profile
        if user.role == User.Role.DOCTOR:
            DoctorProfile.objects.create(user=user)

        # Specify the backend explicitly
        backend = get_backends()[0]
        user.backend = f"{backend.__module__}.{backend.__class__.__name__}"
        login(self.request, user)

        # Redirect based on role
        if user.is_doctor():
            messages.success(self.request, "Registration successful! Please complete your doctor profile.")
            return HttpResponseRedirect(reverse_lazy('update_doctor_profile'))
        else:
            messages.success(self.request, "Registration successful!")
            return HttpResponseRedirect(reverse_lazy('patient_dashboard'))

    
    def form_invalid(self, form):
        messages.error(self.request, "Registration failed. Please correct the errors below.")
        return super().form_invalid(form)

class ProfileUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating the user profile."""
    model = Profile
    form_class = ProfileForm
    template_name = 'auth/edit_profile.html'
    success_url = reverse_lazy('profile')
    
    def get_object(self, queryset=None):
        # Get or create profile for current user
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully!")
        return super().form_valid(form)

class DoctorProfileUpdateView(LoginRequiredMixin, DoctorRequiredMixin, UpdateView):
    """View for updating doctor-specific profile information."""
    model = DoctorProfile
    form_class = DoctorProfileForm
    template_name = 'auth/update_doctor_profile.html'
    success_url = reverse_lazy('doctor_dashboard')
    
    def get_object(self, queryset=None):
        # Get or create doctor profile for current user
        profile, created = DoctorProfile.objects.get_or_create(user=self.request.user)
        return profile
    
    def form_valid(self, form):
        messages.success(self.request, "Doctor profile updated successfully!")
        return super().form_valid(form)

class ProfileView(LoginRequiredMixin, DetailView):
    """View for displaying user profile information."""
    model = User
    template_name = 'auth/profile.html'
    context_object_name = 'user'
    
    def get_object(self, queryset=None):
        return self.request.user
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add profile data to context
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        context['profile'] = profile
        
        # If user is a doctor, add doctor profile data to context
        if self.request.user.is_doctor():
            doctor_profile, created = DoctorProfile.objects.get_or_create(user=self.request.user)
            context['doctor_profile'] = doctor_profile
        
        return context

class PatientDashboardView(LoginRequiredMixin, PatientRequiredMixin, TemplateView):
    """Dashboard view for patients."""
    template_name = 'patient/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Additional context for patient dashboard can be added here
        return context

class DoctorDashboardView(LoginRequiredMixin, DoctorRequiredMixin, TemplateView):
    """Dashboard view for doctors."""
    template_name = 'doctor/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Additional context for doctor dashboard can be added here
        return context

class AdminDashboardView(LoginRequiredMixin, AdminRequiredMixin, TemplateView):
    """Dashboard view for admins."""
    template_name = 'admin/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add summary statistics for the admin dashboard
        context['total_users'] = User.objects.count()
        context['total_doctors'] = User.objects.filter(role=User.Role.DOCTOR).count()
        context['total_patients'] = User.objects.filter(role=User.Role.PATIENT).count()
        
        # Additional context for admin dashboard can be added here
        return context
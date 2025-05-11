from django.urls import path
from .views import (
    CustomLoginView, CustomLogoutView, RegisterView, 
    ProfileUpdateView, DoctorProfileUpdateView, ProfileView,
    PatientDashboardView, DoctorDashboardView, AdminDashboardView,
)

urlpatterns = [
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('profile/edit/', ProfileUpdateView.as_view(), name='edit_profile'),
    path('profile/doctor/update/', DoctorProfileUpdateView.as_view(), name='update_doctor_profile'),
    path('dashboard/patient/', PatientDashboardView.as_view(), name='patient_dashboard'),
    path('dashboard/doctor/', DoctorDashboardView.as_view(), name='doctor_dashboard'),
    path('dashboard/admin/', AdminDashboardView.as_view(), name='admin_dashboard'),
]

from django.contrib import admin
from .models import Availability, Appointment, Service, Testimonial, HealthTip

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    """Admin interface for the Availability model."""
    list_display = ('doctor', 'date', 'start_time', 'end_time', 'is_booked')
    list_filter = ('date', 'is_booked', 'doctor')
    search_fields = ('doctor__email', 'doctor__first_name', 'doctor__last_name')
    date_hierarchy = 'date'

@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    """Admin interface for the Appointment model."""
    list_display = ('id', 'patient', 'doctor', 'appointment_date', 'appointment_time', 'status')
    list_filter = ('status', 'appointment_date', 'doctor')
    search_fields = ('patient__email', 'doctor__email', 'patient__first_name', 'doctor__first_name')
    date_hierarchy = 'appointment_date'
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    """Admin interface for the Service model."""
    list_display = ('name', 'display_order', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    list_editable = ('display_order', 'is_active')
    ordering = ('display_order', 'name')

@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin interface for the Testimonial model."""
    list_display = ('name', 'rating', 'is_featured', 'is_approved', 'created_at')
    list_filter = ('rating', 'is_featured', 'is_approved')
    search_fields = ('name', 'content', 'patient__email')
    list_editable = ('is_featured', 'is_approved')
    ordering = ('-is_featured', '-created_at')

@admin.register(HealthTip)
class HealthTipAdmin(admin.ModelAdmin):
    """Admin interface for the HealthTip model."""
    list_display = ('title', 'author', 'is_featured', 'created_at')
    list_filter = ('is_featured', 'author')
    search_fields = ('title', 'content', 'author__email')
    list_editable = ('is_featured',)
    ordering = ('-is_featured', '-created_at')

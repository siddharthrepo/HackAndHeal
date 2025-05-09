from django.db import models
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.core.exceptions import ValidationError
from auth_app.models import User, DoctorProfile
import uuid

class Availability(models.Model):
    """Doctor availability slots model."""
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='availabilities')
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    is_booked = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('doctor', 'date', 'start_time')
        ordering = ['date', 'start_time']
    
    def __str__(self):
        return f"Dr. {self.doctor.get_full_name()} - {self.date} {self.start_time} to {self.end_time}"
    
    def clean(self):
        """Validate that start_time is before end_time."""
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")
    
    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
    
    @property
    def is_past(self):
        """Check if the availability slot is in the past."""
        now = timezone.now()
        slot_datetime = timezone.make_aware(
            timezone.datetime.combine(self.date, self.start_time)
        )
        return slot_datetime < now

class Appointment(models.Model):
    """Model for storing appointment information."""
    class Status(models.TextChoices):
        REQUESTED = 'REQUESTED', 'Requested'
        CONFIRMED = 'CONFIRMED', 'Confirmed'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        NO_SHOW = 'NO_SHOW', 'No Show'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_appointments'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_appointments'
    )
    availability = models.OneToOneField(
        Availability, 
        on_delete=models.CASCADE, 
        related_name='appointment',
        null=True
    )
    appointment_date = models.DateField()
    appointment_time = models.TimeField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.REQUESTED)
    reason = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    video_room_id = models.CharField(max_length=255, blank=True, null=True)
    video_room_token = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-appointment_date', '-appointment_time']
    
    def __str__(self):
        return f"{self.patient.get_full_name()} with Dr. {self.doctor.get_full_name()} on {self.appointment_date} {self.appointment_time}"
    
    def get_absolute_url(self):
        return reverse('appointment_detail', kwargs={'pk': self.pk})
    
    @property
    def is_past(self):
        """Check if the appointment is in the past."""
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime < now
    
    @property
    def is_today(self):
        """Check if the appointment is today."""
        today = timezone.now().date()
        return self.appointment_date == today
    
    @property
    def can_join(self):
        """Check if it's time to join the appointment (within 15 minutes before)."""
        if not self.is_today or self.status != self.Status.CONFIRMED:
            return False
        
        now = timezone.now()
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        
        time_diff = appointment_datetime - now
        return time_diff.total_seconds() <= 900 and time_diff.total_seconds() > -3600  # 15 min before to 1 hour after

class Service(models.Model):
    """Model for healthcare services offered on the platform."""
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_class = models.CharField(max_length=100, help_text="FontAwesome or custom icon class")
    display_order = models.PositiveIntegerField(default=0, help_text="Order to display services (lowest first)")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return self.name
        
class Testimonial(models.Model):
    """Model for patient testimonials displayed on the platform."""
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='testimonials'
    )
    name = models.CharField(max_length=100, help_text="Can be anonymous or use patient name")
    image = models.URLField(blank=True, null=True, help_text="Profile image URL")
    content = models.TextField()
    rating = models.PositiveSmallIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])
    is_featured = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return f"Testimonial by {self.name}"
    
    @property
    def display_name(self):
        if self.patient:
            return self.patient.get_full_name()
        return self.name

class HealthTip(models.Model):
    """Model for health tips and articles displayed on the platform."""
    title = models.CharField(max_length=200)
    content = models.TextField()
    image_url = models.URLField(blank=True, null=True)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='health_tips'
    )
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
    
    def __str__(self):
        return self.title
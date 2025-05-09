from django import forms
from django.utils import timezone
from .models import Availability, Appointment

class AvailabilityForm(forms.ModelForm):
    """Form for doctors to create new availability slots."""
    date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'w-full px-4 py-2 border rounded-md'}),
        help_text="Select a date for your availability"
    )
    start_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border rounded-md'}),
        help_text="Start time of your availability"
    )
    end_time = forms.TimeField(
        widget=forms.TimeInput(attrs={'type': 'time', 'class': 'w-full px-4 py-2 border rounded-md'}),
        help_text="End time of your availability"
    )
    
    class Meta:
        model = Availability
        fields = ['date', 'start_time', 'end_time']
    
    def clean(self):
        cleaned_data = super().clean()
        date = cleaned_data.get('date')
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        
        if date and start_time and end_time:
            # Check if date is in the future
            if date < timezone.now().date():
                raise forms.ValidationError("Availability date cannot be in the past.")
            
            # Check if start time is before end time
            if start_time >= end_time:
                raise forms.ValidationError("Start time must be before end time.")
        
        return cleaned_data

class AppointmentForm(forms.ModelForm):
    """Form for patients to book appointments."""
    reason = forms.CharField(
        required=True,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'w-full px-4 py-2 border rounded-md'}),
        help_text="Please briefly describe your reason for consultation"
    )
    
    class Meta:
        model = Appointment
        fields = ['reason']

class DoctorSearchForm(forms.Form):
    """Form for searching doctors."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-md',
            'placeholder': 'Search by name, specialty...'
        })
    )
    specialty = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-2 border rounded-md',
            'placeholder': 'Specialty (e.g., Cardiology)'
        })
    )
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'type': 'date',
            'class': 'w-full px-4 py-2 border rounded-md'
        })
    )

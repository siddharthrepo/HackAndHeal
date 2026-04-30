from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import Availability, Appointment, Prescription, PrescriptionItem, FollowUp

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


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['diagnosis', 'instructions', 'doctor_signature_text']
        widgets = {
            'diagnosis': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': 'Enter diagnosis...'}),
            'instructions': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': 'General instructions for the patient...'}),
            'doctor_signature_text': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Dr. Sharma, MBBS, MD'}),
        }


class PrescriptionItemForm(forms.ModelForm):
    class Meta:
        model = PrescriptionItem
        fields = ['medication_name', 'dosage', 'frequency', 'duration', 'notes']
        widgets = {
            'medication_name': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'Medication name'}),
            'dosage': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 500mg'}),
            'frequency': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. Twice daily'}),
            'duration': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'e.g. 7 days'}),
            'notes': forms.TextInput(attrs={'class': 'form-input', 'placeholder': 'After meals, etc.'}),
        }


PrescriptionItemFormSet = inlineformset_factory(
    Prescription,
    PrescriptionItem,
    form=PrescriptionItemForm,
    extra=3,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class FollowUpForm(forms.ModelForm):
    class Meta:
        model = FollowUp
        fields = ['follow_up_date', 'notes']
        widgets = {
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-input'}),
            'notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-textarea', 'placeholder': 'Follow-up notes...'}),
        }

    def clean_follow_up_date(self):
        date = self.cleaned_data.get('follow_up_date')
        if date and date <= timezone.now().date():
            raise forms.ValidationError("Follow-up date must be in the future.")
        return date

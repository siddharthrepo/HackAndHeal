from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import User, Profile, DoctorProfile
from django.contrib.auth import get_user_model
class CustomAuthenticationForm(AuthenticationForm):
    """Custom authentication form with styling."""
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Email'})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Password'})
    )

class UserRegistrationForm(UserCreationForm):
    """Form for user registration."""
    role = forms.ChoiceField(
        choices=[(User.Role.PATIENT, 'Patient'), (User.Role.DOCTOR, 'Doctor')],
        widget=forms.RadioSelect(attrs={'class': 'mr-2'}),
        initial=User.Role.PATIENT
    )
    
    first_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'First Name'})
    )
    
    last_name = forms.CharField(
        max_length=30,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Last Name'})
    )
    
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Email'})
    )
    
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Password'})
    )
    
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Confirm Password'})
    )
    
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'password1', 'password2', 'role')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Email already exists")
        return email

class ProfileForm(forms.ModelForm):
    """Form for user profile information."""
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Phone Number'})
    )
    
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'rows': 3, 'placeholder': 'Address'})
    )
    
    date_of_birth = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'type': 'date'})
    )
    
    class Meta:
        model = Profile
        fields = ('phone_number', 'address', 'date_of_birth')

class DoctorProfileForm(forms.ModelForm):
    """Form for doctor-specific profile information."""
    specialty = forms.CharField(
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Specialty'})
    )
    
    license_number = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'License Number'})
    )
    
    experience_years = forms.IntegerField(
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Years of Experience'})
    )
    
    bio = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'rows': 5, 'placeholder': 'Professional Bio'})
    )
    
    consultation_fee = forms.DecimalField(
        max_digits=10,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Consultation Fee (INR)'})
    )
    
    education = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'rows': 3, 'placeholder': 'Education & Qualifications'})
    )
    
    hospital_affiliation = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Hospital Affiliation'})
    )
    
    languages_spoken = forms.CharField(
        required=False,
        max_length=255,
        widget=forms.TextInput(attrs={'class': 'w-full px-4 py-2 border rounded-md', 'placeholder': 'Languages Spoken'})
    )
    
User = get_user_model()

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['phone_number', 'address', 'date_of_birth']

class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = [
            'specialty', 'license_number', 'experience_years',
            'consultation_fee', 'bio', 'education',
            'hospital_affiliation', 'languages_spoken'
        ]
    class Meta:
        model = DoctorProfile
        fields = ('specialty', 'license_number', 'experience_years', 'bio', 
                 'consultation_fee', 'education', 'hospital_affiliation', 
                 'languages_spoken')

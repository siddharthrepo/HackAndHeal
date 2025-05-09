from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):
    """Custom manager for User model with email as the unique identifier"""
    def create_user(self, email, password=None, **extra_fields):
        """Create and save a regular user with the given email and password."""
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """Create and save a superuser with the given email and password."""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)
        
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))
        
        return self.create_user(email, password, **extra_fields)

class User(AbstractUser):
    """Custom User model with email authentication and role-based access"""
    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        DOCTOR = 'DOCTOR', _('Doctor')
        PATIENT = 'PATIENT', _('Patient')
    
    email = models.EmailField(_('email address'), unique=True)
    role = models.CharField(max_length=10, choices=Role.choices, default=Role.PATIENT)
    is_verified = models.BooleanField(default=False)
    
    # Make username field optional as we'll use email for authentication
    username = models.CharField(max_length=150, blank=True, null=True)
    
    # Use email as the primary field for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []
    
    objects = UserManager()
    
    def __str__(self):
        return self.email
    
    def is_admin(self):
        return self.role == self.Role.ADMIN
    
    def is_doctor(self):
        return self.role == self.Role.DOCTOR
    
    def is_patient(self):
        return self.role == self.Role.PATIENT

class Profile(models.Model):
    """Additional information about a user."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    profile_picture = models.URLField(blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.email}'s profile"

class DoctorProfile(models.Model):
    """Additional information specific to doctors."""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    specialty = models.CharField(max_length=100, blank=True, null=True)
    license_number = models.CharField(max_length=50, blank=True, null=True)
    experience_years = models.PositiveIntegerField(blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    hospital_affiliation = models.CharField(max_length=255, blank=True, null=True)
    languages_spoken = models.CharField(max_length=255, blank=True, null=True)
    is_available = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Dr. {self.user.get_full_name() or self.user.email}"

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile, DoctorProfile

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin interface for the custom User model."""
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Role'), {'fields': ('role',)}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser',
                                      'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role'),
        }),
    )
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Admin interface for the Profile model."""
    list_display = ('user', 'phone_number', 'created_at')
    search_fields = ('user__email', 'phone_number')
    list_filter = ('created_at',)

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    """Admin interface for the DoctorProfile model."""
    list_display = ('user', 'specialty', 'experience_years', 'is_available')
    search_fields = ('user__email', 'specialty')
    list_filter = ('specialty', 'experience_years', 'is_available')

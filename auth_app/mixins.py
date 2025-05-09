from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from django.urls import reverse_lazy

class RoleRequiredMixin(UserPassesTestMixin):
    """Base mixin for role-based access control."""
    role_required = None
    
    def test_func(self):
        """Check if the user has the required role."""
        # All users must be authenticated
        if not self.request.user.is_authenticated:
            return False
        
        # Check role if specified
        if self.role_required:
            return self.request.user.role == self.role_required
        
        # Default: allow access
        return True
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return redirect(reverse_lazy('login'))
        raise PermissionDenied("You don't have permission to access this page.")

class AdminRequiredMixin(RoleRequiredMixin):
    """Mixin that requires the user to be an admin."""
    def test_func(self):
        """Check if the user is an admin."""
        return self.request.user.is_authenticated and self.request.user.is_admin()

class DoctorRequiredMixin(RoleRequiredMixin):
    """Mixin that requires the user to be a doctor."""
    def test_func(self):
        """Check if the user is a doctor."""
        return self.request.user.is_authenticated and self.request.user.is_doctor()

class PatientRequiredMixin(RoleRequiredMixin):
    """Mixin that requires the user to be a patient."""
    def test_func(self):
        """Check if the user is a patient."""
        return self.request.user.is_authenticated and self.request.user.is_patient()

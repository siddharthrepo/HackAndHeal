from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()

class EmailBackend(ModelBackend):
    """
    Custom authentication backend for authenticating with email.
    """
    def authenticate(self, request, username=None, password=None, **kwargs):
        # Check if the username provided is actually an email
        try:
            # Try to find a user that matches the email
            user = User.objects.get(email=username)
            
            # Check the password for that user
            if user.check_password(password):
                return user
            
        except User.DoesNotExist:
            # If no user found with that email, return None (authentication fails)
            return None
        
        # If the password check fails, return None (authentication fails)
        return None
    
    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

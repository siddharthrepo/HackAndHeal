from django.db import models
from django.conf import settings
from consultation_app.models import Appointment

class ChatMessage(models.Model):
    """Model for storing chat messages."""
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name='chat_messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.email} - {self.created_at.strftime('%d/%m/%Y %H:%M')}"

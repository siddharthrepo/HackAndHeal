from django.shortcuts import render, get_object_or_404
from django.views.generic import ListView, View
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from consultation_app.models import Appointment
from .models import ChatMessage

class ChatHistoryView(LoginRequiredMixin, ListView):
    """
    View for displaying chat history for an appointment.
    """
    model = ChatMessage
    template_name = 'chat/chat_history.html'
    context_object_name = 'messages'
    
    def get_queryset(self):
        # Get the appointment
        appointment_id = self.kwargs.get('appointment_id')
        self.appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        if self.request.user != self.appointment.patient and self.request.user != self.appointment.doctor:
            raise PermissionDenied("You don't have permission to view this chat.")
        
        # Mark messages as read if we're not the sender
        unread_messages = ChatMessage.objects.filter(
            appointment=self.appointment,
            is_read=False
        ).exclude(sender=self.request.user)
        
        for message in unread_messages:
            message.is_read = True
            message.save()
        
        # Return all messages for this appointment
        return ChatMessage.objects.filter(appointment=self.appointment).order_by('created_at')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['appointment'] = self.appointment
        context['is_doctor'] = self.request.user.is_doctor()
        return context

class LoadMessagesView(LoginRequiredMixin, View):
    """
    AJAX view for loading messages.
    """
    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)
        
        # Check permissions
        if request.user != appointment.patient and request.user != appointment.doctor:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get last message ID from request to only fetch new messages
        last_message_id = request.GET.get('last_message_id', 0)
        
        # Mark messages as read if we're not the sender
        unread_messages = ChatMessage.objects.filter(
            appointment=appointment,
            is_read=False
        ).exclude(sender=request.user)
        
        for message in unread_messages:
            message.is_read = True
            message.save()
        
        # Fetch new messages
        messages = ChatMessage.objects.filter(
            appointment=appointment,
            id__gt=last_message_id
        ).order_by('created_at')
        
        # Format messages for JSON response
        messages_data = []
        for message in messages:
            messages_data.append({
                'id': message.id,
                'sender_id': message.sender.id,
                'sender_name': message.sender.get_full_name() or message.sender.email,
                'message': message.message,
                'is_self': message.sender.id == request.user.id,
                'timestamp': message.created_at.strftime('%I:%M %p')
            })
        
        return JsonResponse({'messages': messages_data})

import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone
from django.contrib.auth import get_user_model
from consultation_app.models import Appointment
from .models import ChatMessage

User = get_user_model()

class ChatConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for handling real-time chat.
    """
    async def connect(self):
        """
        Connect to WebSocket and join appointment-specific group.
        """
        # Get appointment ID from URL
        self.appointment_id = self.scope['url_route']['kwargs']['appointment_id']
        self.room_group_name = f'chat_{self.appointment_id}'
        
        # Check if user has permission to join this chat
        if not await self.user_can_access_appointment():
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """
        Leave the appointment-specific group.
        """
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """
        Receive message from WebSocket and broadcast to the group.
        """
        data = json.loads(text_data)
        message = data.get('message', '').strip()
        
        if not message:
            return
        
        # Get user info
        user_id = self.scope['user'].id
        user = await self.get_user(user_id)
        
        # Save message to database
        chat_message = await self.save_message(message, user)
        
        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'sender_id': user_id,
                'sender_name': user.get_full_name() or user.email,
                'message_id': chat_message.id,
                'timestamp': timezone.now().strftime('%I:%M %p')
            }
        )
    
    async def chat_message(self, event):
        """
        Receive message from room group and send to WebSocket.
        """
        await self.send(text_data=json.dumps({
            'message_id': event['message_id'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'message': event['message'],
            'is_self': event['sender_id'] == self.scope['user'].id,
            'timestamp': event['timestamp']
        }))
    
    @database_sync_to_async
    def user_can_access_appointment(self):
        """
        Check if user has permission to access this appointment.
        """
        user = self.scope['user']
        
        # Make sure user is authenticated
        if not user.is_authenticated:
            return False
        
        try:
            appointment = Appointment.objects.get(id=self.appointment_id)
            return user == appointment.patient or user == appointment.doctor
        except Appointment.DoesNotExist:
            return False
    
    @database_sync_to_async
    def get_user(self, user_id):
        """
        Get user object from database.
        """
        return User.objects.get(id=user_id)
    
    @database_sync_to_async
    def save_message(self, message, user):
        """
        Save message to database.
        """
        appointment = Appointment.objects.get(id=self.appointment_id)
        chat_message = ChatMessage.objects.create(
            appointment=appointment,
            sender=user,
            message=message,
            is_read=False
        )
        return chat_message

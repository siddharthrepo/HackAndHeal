from django.urls import path
from .views import ChatHistoryView, LoadMessagesView

urlpatterns = [
    path('appointment/<uuid:appointment_id>/', ChatHistoryView.as_view(), name='chat_history'),
    path('appointment/<uuid:appointment_id>/messages/', LoadMessagesView.as_view(), name='load_messages'),
]

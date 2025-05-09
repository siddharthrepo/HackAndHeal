from django.urls import path
from .views import PaymentCheckoutView, PaymentCallbackView, ReceiptDetailView

urlpatterns = [
    path('checkout/<uuid:appointment_id>/', PaymentCheckoutView.as_view(), name='payment_checkout'),
    path('callback/', PaymentCallbackView.as_view(), name='payment_callback'),
    path('receipt/<uuid:pk>/', ReceiptDetailView.as_view(), name='receipt_detail'),
]

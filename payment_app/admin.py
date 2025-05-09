from django.contrib import admin
from .models import Payment, Receipt

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for the Payment model."""
    list_display = ('id', 'appointment', 'patient', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('patient__email', 'razorpay_order_id', 'razorpay_payment_id')
    readonly_fields = ('id', 'created_at', 'updated_at')

@admin.register(Receipt)
class ReceiptAdmin(admin.ModelAdmin):
    """Admin interface for the Receipt model."""
    list_display = ('receipt_number', 'patient_name', 'doctor_name', 'amount', 'payment_date')
    search_fields = ('receipt_number', 'patient_name', 'doctor_name')
    readonly_fields = ('id', 'created_at')

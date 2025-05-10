import razorpay
import json
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import View, DetailView
from django.urls import reverse
from django.http import JsonResponse, HttpResponseBadRequest
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from consultation_app.models import Appointment
from .models import Payment, Receipt
from datetime import datetime
import hmac
import hashlib

class PaymentCheckoutView(LoginRequiredMixin, View):
    def get(self, request, appointment_id):
        appointment = get_object_or_404(Appointment, id=appointment_id)

        if request.user != appointment.patient:
            messages.error(request, "You don't have permission to make this payment.")
            return redirect('home')

        # Check if payment already exists
        try:
            payment = Payment.objects.get(appointment=appointment)
            if payment.status == Payment.Status.COMPLETED:
                messages.info(request, "This appointment has already been paid for.")
                return redirect('appointment_detail', pk=appointment.id)
        except Payment.DoesNotExist:
            payment = None

        if not settings.RAZORPAY_ENABLED:
            # Simulate successful payment
            if not payment:
                payment = Payment.objects.create(
                    appointment=appointment,
                    patient=request.user,
                    amount=appointment.doctor.doctor_profile.consultation_fee,
                    currency="INR",
                    razorpay_order_id="SIMULATED_ORDER_ID",
                    status=Payment.Status.COMPLETED
                )
            else:
                payment.status = Payment.Status.COMPLETED
                payment.razorpay_order_id = "SIMULATED_ORDER_ID"
                payment.save()

            messages.success(request, "Payment has been simulated successfully.")
            return redirect('appointment_detail', pk=appointment.id)

        # Existing Razorpay logic below if enabled
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        amount = int(appointment.doctor.doctor_profile.consultation_fee * 100)  # paisa
        currency = "INR"

        if not payment or not payment.razorpay_order_id:
            data = {
                'amount': amount,
                'currency': currency,
                'receipt': f"receipt_{appointment.id}",
                'notes': {
                    'appointment_id': str(appointment.id),
                    'patient_email': appointment.patient.email,
                    'doctor_name': appointment.doctor.get_full_name()
                }
            }
            razorpay_order = client.order.create(data=data)
            order_id = razorpay_order['id']

            if not payment:
                payment = Payment.objects.create(
                    appointment=appointment,
                    patient=request.user,
                    amount=appointment.doctor.doctor_profile.consultation_fee,
                    currency=currency,
                    razorpay_order_id=order_id,
                    status=Payment.Status.PENDING
                )
            else:
                payment.razorpay_order_id = order_id
                payment.amount = appointment.doctor.doctor_profile.consultation_fee
                payment.save()
        else:
            order_id = payment.razorpay_order_id
            amount = int(payment.amount * 100)

        context = {
            'appointment': appointment,
            'payment': payment,
            'order_id': order_id,
            'amount': payment.amount,
            'amount_in_paisa': amount,
            'currency': 'INR',
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'callback_url': request.build_absolute_uri(reverse('payment_callback')),
            'doctor_profile': appointment.doctor.doctor_profile
        }

        return render(request, 'payment/checkout.html', context)

@method_decorator(csrf_exempt, name='dispatch')
class PaymentCallbackView(View):
    """
    View to handle payment callback from Razorpay.
    """
    def post(self, request):
        # Get payment details from POST request
        razorpay_payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        razorpay_signature = request.POST.get('razorpay_signature', '')
        
        # Verify the payment signature
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        try:
            # Find the payment
            payment = get_object_or_404(Payment, razorpay_order_id=razorpay_order_id)
            
            # Verify signature
            params_dict = {
                'razorpay_order_id': razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature': razorpay_signature
            }
            
            client.utility.verify_payment_signature(params_dict)
            
            # Update payment status
            payment.razorpay_payment_id = razorpay_payment_id
            payment.razorpay_signature = razorpay_signature
            payment.status = Payment.Status.COMPLETED
            payment.save()
            
            # Update appointment status
            appointment = payment.appointment
            appointment.status = Appointment.Status.CONFIRMED
            appointment.save()
            
            # Generate receipt
            self.generate_receipt(payment)
            
            messages.success(request, "Payment successful! Your appointment is confirmed.")
            return redirect('appointment_detail', pk=appointment.id)
            
        except razorpay.errors.SignatureVerificationError:
            messages.error(request, "Payment verification failed. Please contact support.")
            return redirect('home')
        
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            return redirect('home')
    
    def generate_receipt(self, payment):
        """
        Generate a receipt for a completed payment.
        """
        appointment = payment.appointment
        
        # Generate receipt number
        receipt_number = f"R{timezone.now().strftime('%Y%m%d')}-{payment.id.hex[:6]}"
        
        # Calculate tax (assuming 18% GST)
        tax_rate = 0.18
        tax_amount = payment.amount * tax_rate
        total_amount = payment.amount + tax_amount
        
        # Create receipt
        Receipt.objects.create(
            payment=payment,
            receipt_number=receipt_number,
            patient_name=appointment.patient.get_full_name() or appointment.patient.email,
            doctor_name=appointment.doctor.get_full_name() or appointment.doctor.email,
            appointment_date=appointment.appointment_date,
            appointment_time=appointment.appointment_time,
            amount=payment.amount,
            tax_amount=tax_amount,
            total_amount=total_amount,
            payment_date=timezone.now()
        )

class ReceiptDetailView(LoginRequiredMixin, DetailView):
    """
    View for displaying a payment receipt.
    """
    model = Receipt
    template_name = 'payment/receipt.html'
    context_object_name = 'receipt'
    
    def get_object(self, queryset=None):
        receipt = super().get_object(queryset)
        
        # Check if user has permission to view this receipt
        payment = receipt.payment
        
        if self.request.user != payment.patient and self.request.user != payment.appointment.doctor and not self.request.user.is_admin():
            messages.error(self.request, "You don't have permission to view this receipt.")
            return None
        
        return receipt

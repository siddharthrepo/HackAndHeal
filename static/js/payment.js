/**
 * Payment functionality for Chikitsa360
 * Integrates Razorpay for payment processing
 */

// Initialize global variables
let razorpayInstance = null;

document.addEventListener('DOMContentLoaded', function() {
    const checkoutForm = document.getElementById('checkout-form');
    const razorpayButton = document.getElementById('razorpay-button');
    
    // Initialize Razorpay if needed
    if (razorpayButton) {
        initializeRazorpay();
    }
    
    /**
     * Initialize Razorpay
     */
    function initializeRazorpay() {
        // Get data from data attributes
        const orderId = razorpayButton.dataset.orderId;
        const amount = razorpayButton.dataset.amount;
        const currency = razorpayButton.dataset.currency || 'INR';
        const name = razorpayButton.dataset.name || 'Chikitsa360';
        const description = razorpayButton.dataset.description || 'Doctor Consultation';
        const keyId = razorpayButton.dataset.keyId;
        const prefill = {
            name: razorpayButton.dataset.userName || '',
            email: razorpayButton.dataset.userEmail || '',
            contact: razorpayButton.dataset.userPhone || ''
        };
        const callbackUrl = razorpayButton.dataset.callbackUrl;
        
        // Add event listener to the button
        razorpayButton.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Display loading state
            razorpayButton.disabled = true;
            razorpayButton.textContent = 'Processing...';
            razorpayButton.classList.add('opacity-70');
            
            // Create Razorpay options
            const options = {
                key: keyId,
                amount: Math.round(amount * 100), // Convert to paise
                currency: currency,
                name: name,
                description: description,
                order_id: orderId,
                handler: function(response) {
                    // This function will be called when payment is successful
                    handlePaymentSuccess(response);
                },
                prefill: prefill,
                notes: {
                    order_id: orderId
                },
                theme: {
                    color: '#3B82F6' // Blue color from Tailwind
                },
                modal: {
                    ondismiss: function() {
                        // Reset button state
                        razorpayButton.disabled = false;
                        razorpayButton.textContent = 'Pay Now';
                        razorpayButton.classList.remove('opacity-70');
                    }
                }
            };
            
            // Create Razorpay instance and open payment modal
            razorpayInstance = new Razorpay(options);
            razorpayInstance.open();
        });
    }
    
    /**
     * Handle successful payment
     */
    function handlePaymentSuccess(response) {
        // Get the form
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = document.getElementById('callback-url').value;
        
        // Add CSRF token
        const csrfTokenInput = document.createElement('input');
        csrfTokenInput.type = 'hidden';
        csrfTokenInput.name = 'csrfmiddlewaretoken';
        csrfTokenInput.value = document.querySelector('[name=csrfmiddlewaretoken]').value;
        form.appendChild(csrfTokenInput);
        
        // Add payment details
        for (const key in response) {
            if (response.hasOwnProperty(key)) {
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = key;
                input.value = response[key];
                form.appendChild(input);
            }
        }
        
        // Display loading message
        const loadingMessage = document.createElement('div');
        loadingMessage.className = 'fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50';
        loadingMessage.innerHTML = `
            <div class="bg-white p-5 rounded-lg shadow-lg text-center">
                <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                <p class="text-lg font-semibold">Processing your payment...</p>
                <p class="text-gray-600">Please do not close this window.</p>
            </div>
        `;
        document.body.appendChild(loadingMessage);
        
        // Submit the form to complete the payment
        document.body.appendChild(form);
        form.submit();
    }
    
    /**
     * Format currency amount
     */
    function formatCurrency(amount, currency = 'INR') {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: currency
        }).format(amount);
    }
    
    // Update price displays if needed
    document.querySelectorAll('.format-currency').forEach(element => {
        const amount = parseFloat(element.textContent);
        if (!isNaN(amount)) {
            element.textContent = formatCurrency(amount);
        }
    });
    
    // Add validation to checkout form if present
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            // Form validation can be added here if needed
            // We're using Razorpay's UI so minimal validation needed
        });
    }
});

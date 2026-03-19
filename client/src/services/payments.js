// src/services/payments.js - Payment and Subscription service
import { paymentApi, handleResponse } from './api';
import config from './config';
import { toast } from 'react-toastify';

// Load Razorpay script dynamically
const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    // Check if already loaded
    if (window.Razorpay) {
      resolve(true);
      return;
    }
    
    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => {
      console.log('✅ Razorpay script loaded');
      resolve(true);
    };
    script.onerror = () => {
      console.error('❌ Failed to load Razorpay script');
      resolve(false);
    };
    document.body.appendChild(script);
  });
};

// Plan definitions
const PLANS = {
  monthly: {
    id: 'monthly',
    name: 'Monthly Premium',
    price: 499,
    currency: 'INR',
    duration: 'month',
    priceLabel: '₹499/month',
    features: [
      'Unlimited book summaries',
      'AI-powered recommendations',
      'Personalized reading lists',
      'Priority support'
    ]
  },
  yearly: {
    id: 'yearly',
    name: 'Yearly Premium',
    price: 3999,
    currency: 'INR',
    duration: 'year',
    priceLabel: '₹3999/year',
    savings: 'Save ₹1989 (33% off)',
    features: [
      'Everything in Monthly',
      '2 months free',
      'Early access to new features',
      'Premium support'
    ]
  },
  lifetime: {
    id: 'lifetime',
    name: 'Lifetime Access',
    price: 9999,
    currency: 'INR',
    duration: 'lifetime',
    priceLabel: '₹9999 one-time',
    savings: 'Best value',
    features: [
      'Everything in Yearly',
      'Lifetime updates',
      'Beta features access',
      'VIP support'
    ]
  }
};

export const paymentService = {
  // Get subscription status
  async getSubscriptionStatus(userId) {
    if (!userId) return { is_active: false };
    
    const result = await handleResponse(
      paymentApi.get(`/subscription/${userId}`)
    );
    
    if (result.success) {
      return result.data;
    }
    
    return { is_active: false };
  },

  // Get plan details
  getPlanDetails(planId) {
    return PLANS[planId] || PLANS.monthly;
  },

  // Get all plans
  getAllPlans() {
    return Object.values(PLANS);
  },

  // Create Razorpay order
  async createOrder(userId, email, planId) {
    const result = await handleResponse(
      paymentApi.post('/create-order', {
        user_id: userId,
        email,
        plan_id: planId
      })
    );
    
    return result;
  },

  // Initialize Razorpay payment
  async initiatePayment(userId, email, planId, onSuccess, onFailure) {
    try {
      // Check if using mock payments (for development)
      if (config.ENABLE_MOCK_PAYMENTS) {
        console.warn('⚠️ Using MOCK payment mode');
        const result = await this.mockSimulatePaymentSuccess(userId, email, planId);
        if (result.success) {
          toast.success('🎉 [MOCK] Payment successful! Your subscription is now active.');
          if (onSuccess) onSuccess(result.data);
        } else {
          if (onFailure) onFailure(result.error);
        }
        return;
      }

      // Load Razorpay script
      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        toast.error('Failed to load payment gateway. Please try again.');
        if (onFailure) onFailure('Razorpay script failed to load');
        return;
      }

      // Create order from backend
      const orderResult = await this.createOrder(userId, email, planId);
      
      if (!orderResult.success) {
        toast.error(orderResult.error || 'Failed to create order');
        if (onFailure) onFailure(orderResult.error);
        return;
      }
      
      const orderData = orderResult.data;
      
      // Get plan details for display
      const planDetails = this.getPlanDetails(planId);

      // Razorpay options
      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: config.APP_NAME,
        description: `${planDetails.name} Subscription`,
        image: '/logo.png', // Add your logo path
        order_id: orderData.order_id,
        handler: async function(response) {
          // Verify payment on backend
          try {
            const verifyResult = await handleResponse(
              paymentApi.post('/verify-payment', {
                razorpay_order_id: response.razorpay_order_id,
                razorpay_payment_id: response.razorpay_payment_id,
                razorpay_signature: response.razorpay_signature
              })
            );

            if (verifyResult.success) {
              toast.success('🎉 Payment successful! Your subscription is now active.');
              if (onSuccess) onSuccess(verifyResult.data);
            } else {
              toast.error(verifyResult.error || 'Payment verification failed');
              if (onFailure) onFailure(verifyResult.error);
            }
          } catch (error) {
            console.error('Payment verification failed:', error);
            toast.error('Payment verification failed. Please contact support.');
            if (onFailure) onFailure(error);
          }
        },
        prefill: {
          email: email,
          contact: '' // You can collect phone number if needed
        },
        notes: {
          user_id: userId,
          plan_id: planId
        },
        theme: {
          color: '#4F46E5' // Your primary color
        },
        modal: {
          ondismiss: function() {
            toast.info('Payment cancelled');
            if (onFailure) onFailure({ message: 'Payment cancelled by user' });
          }
        }
      };

      // Open Razorpay checkout
      const razorpay = new window.Razorpay(options);
      razorpay.open();

    } catch (error) {
      console.error('Payment initiation failed:', error);
      toast.error('Failed to initiate payment. Please try again.');
      if (onFailure) onFailure(error);
    }
  },

  // Cancel subscription
  async cancelSubscription(userId) {
    const result = await handleResponse(
      paymentApi.post('/cancel-subscription', { user_id: userId })
    );
    
    if (result.success) {
      toast.success('Subscription cancelled successfully');
    } else {
      toast.error(result.error || 'Failed to cancel subscription');
    }
    
    return result;
  },

  // Format price for display
  formatPrice(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount / 100); // Convert from paise to rupees
  },

  // Check if user has active subscription
  hasActiveSubscription(subscriptionData) {
    return subscriptionData?.is_active === true;
  },

  // Get days remaining in subscription
  getDaysRemaining(expiryTimestamp) {
    if (!expiryTimestamp) return 0;
    
    const now = new Date();
    const expiry = new Date(expiryTimestamp * 1000); // Convert from seconds to milliseconds
    const diffTime = expiry - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    return diffDays > 0 ? diffDays : 0;
  },

  // Format expiry date
  formatExpiryDate(expiryTimestamp) {
    if (!expiryTimestamp) return 'N/A';
    
    return new Date(expiryTimestamp * 1000).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  },

  // ============ MOCK METHODS (for development) ============
  async mockCreateCheckoutSession(userId, email, planId) {
    console.warn('⚠️ Using mock checkout session');
    return handleResponse(
      paymentApi.post('/create-checkout-session', {
        user_id: userId,
        email,
        plan_id: planId
      })
    );
  },

  async mockSimulatePaymentSuccess(userId, email, planId) {
    console.warn('⚠️ Using mock payment success');
    return handleResponse(
      paymentApi.post('/mock-payment-success', {
        user_id: userId,
        email,
        plan_id: planId
      })
    );
  }
};
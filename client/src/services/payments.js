import { paymentApi, handleResponse } from './api';
import config from './config';
import { toast } from 'react-toastify';

const loadRazorpayScript = () => {
  return new Promise((resolve) => {
    if (window.Razorpay) {
      resolve(true);
      return;
    }

    const script = document.createElement('script');
    script.src = 'https://checkout.razorpay.com/v1/checkout.js';
    script.onload = () => resolve(true);
    script.onerror = () => resolve(false);
    document.body.appendChild(script);
  });
};

// FIX: prices stored in paise (matching backend) so formatPrice() works correctly.
// Previously stored in rupees (499) but formatPrice divided by 100, showing ₹4 instead of ₹499.
const PLANS = {
  monthly: {
    id: 'monthly',
    name: 'Monthly Premium',
    price: 49900,         // paise
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
    price: 399900,        // paise
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
    price: 999900,        // paise
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
  async getSubscriptionStatus(userId) {
    if (!userId) return { is_active: false };
    const result = await handleResponse(paymentApi.get(`/subscription/${userId}`));
    return result.success ? result.data : { is_active: false };
  },

  getPlanDetails(planId) {
    return PLANS[planId] || PLANS.monthly;
  },

  getAllPlans() {
    return Object.values(PLANS);
  },

  async createOrder(userId, email, planId) {
    return await handleResponse(
      paymentApi.post('/create-order', {
        user_id: Number(userId),
        email,
        plan_id: planId
      })
    );
  },

  async initiatePayment(userId, email, planId, onSuccess, onFailure) {
    try {
      if (config.ENABLE_MOCK_PAYMENTS) {
        const result = await this.mockSimulatePaymentSuccess(userId, email, planId);
        if (result.success) {
          toast.success('🎉 [MOCK] Payment successful! Your subscription is now active.');
          if (onSuccess) onSuccess(result.data);
        } else {
          if (onFailure) onFailure(result.error);
        }
        return;
      }

      const scriptLoaded = await loadRazorpayScript();
      if (!scriptLoaded) {
        toast.error('Failed to load payment gateway. Please try again.');
        if (onFailure) onFailure('Razorpay script failed to load');
        return;
      }

      const orderResult = await this.createOrder(userId, email, planId);
      if (!orderResult.success) {
        toast.error(orderResult.error || 'Failed to create order');
        if (onFailure) onFailure(orderResult.error);
        return;
      }

      const orderData = orderResult.data;
      const planDetails = this.getPlanDetails(planId);

      const options = {
        key: orderData.key_id,
        amount: orderData.amount,
        currency: orderData.currency,
        name: config.APP_NAME,
        description: `${planDetails.name} Subscription`,
        image: '/logo.png',
        order_id: orderData.order_id,
        handler: async function (response) {
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
            toast.error('Payment verification failed. Please contact support.');
            if (onFailure) onFailure(error);
          }
        },
        prefill: {
          email: email,
          contact: ''
        },
        notes: {
          user_id: userId,
          plan_id: planId
        },
        theme: {
          color: '#4F46E5'
        },
        modal: {
          ondismiss: function () {
            toast.info('Payment cancelled');
            if (onFailure) onFailure({ message: 'Payment cancelled by user' });
          }
        }
      };

      const razorpay = new window.Razorpay(options);
      razorpay.open();
    } catch (error) {
      toast.error('Failed to initiate payment. Please try again.');
      if (onFailure) onFailure(error);
    }
  },

  async cancelSubscription(userId) {
    const result = await handleResponse(
      paymentApi.post('/cancel-subscription', {
        user_id: Number(userId)
      })
    );
    if (result.success) {
      toast.success('Subscription cancelled successfully');
    } else {
      toast.error(result.error || 'Failed to cancel subscription');
    }
    return result;
  },

  // FIX: removed the / 100 division — prices in PLANS are now stored in paise,
  // so this correctly converts 49900 paise → ₹499.
  formatPrice(amount, currency = 'INR') {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0,
      maximumFractionDigits: 0
    }).format(amount / 100);
  },

  hasActiveSubscription(subscriptionData) {
    return subscriptionData?.is_active === true;
  },

  getDaysRemaining(expiryTimestamp) {
    if (!expiryTimestamp) return 0;
    const now = new Date();
    const expiry = new Date(expiryTimestamp * 1000);
    const diffTime = expiry - now;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    return diffDays > 0 ? diffDays : 0;
  },

  formatExpiryDate(expiryTimestamp) {
    if (!expiryTimestamp) return 'N/A';
    return new Date(expiryTimestamp * 1000).toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  },

  async mockCreateCheckoutSession(userId, email, planId) {
    return handleResponse(
      paymentApi.post('/create-checkout-session', {
        user_id: Number(userId),
        email,
        plan_id: planId
      })
    );
  },

  async mockSimulatePaymentSuccess(userId, email, planId) {
    return handleResponse(
      paymentApi.post('/mock-payment-success', {
        user_id: Number(userId),
        email,
        plan_id: planId
      })
    );
  },

  async createCheckoutSession(userId, email, planId) {
    if (config.ENABLE_MOCK_PAYMENTS) {
      return this.mockCreateCheckoutSession(userId, email, planId);
    }
    return this.createOrder(userId, email, planId);
  }
};
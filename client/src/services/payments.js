// src/services/payments.js - Payment and Subscription service
import { paymentApi } from './api';

export const paymentService = {
  async createCheckoutSession(userId, email, planId) {
    const response = await paymentApi.post('/create-checkout-session', {
      user_id: userId,
      email,
      plan_id: planId
    });
    return response.data;
  },

  async getSubscriptionStatus(userId) {
    try {
      const response = await paymentApi.get(`/subscription/${userId}`);
      return response.data;
    } catch (error) {
      console.error('Error fetching subscription status:', error);
      return { is_active: false };
    }
  },

  async simulatePaymentSuccess(userId, email, planId) {
    const response = await paymentApi.post('/mock-payment-success', {
      user_id: userId,
      email,
      plan_id: planId
    });
    return response.data;
  }
};

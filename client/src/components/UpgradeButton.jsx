import React, { useState } from 'react';
import { useApp } from '../context/AppContext';
import { paymentService } from '../services/payments';
import { toast } from 'react-toastify';

const UpgradeButton = () => {
  const { user, subscription, checkAuth } = useApp();
  const [loading, setLoading] = useState(false);

  if (!user || subscription?.is_active) return null;

  const handleUpgrade = async () => {
    setLoading(true);
    try {
      // Simulate calling payment service to create a checkout session
      const result = await paymentService.createCheckoutSession(
        user.id,
        user.email,
        'premium_plan'
      );
      
      console.log('🔗 Checkout URL:', result.checkout_url);
      
      // For demo purposes, we'll simulate a successful payment immediately
      toast.info('Simulating payment process...');
      
      setTimeout(async () => {
        const success = await paymentService.simulatePaymentSuccess(
          user.id,
          user.email,
          'premium_plan'
        );
        
        if (success.success) {
          toast.success('Congratulations! You are now a Premium member! 🎉');
          // Re-check auth to update subscription state in context
          window.location.reload(); // Simple way to refresh state
        }
      }, 2000);
      
    } catch (error) {
      toast.error('Failed to initiate upgrade');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <button
      onClick={handleUpgrade}
      disabled={loading}
      className="bg-gradient-to-r from-amber-400 to-amber-600 hover:from-amber-500 hover:to-amber-700 text-white font-bold py-2 px-4 rounded-full shadow-lg transform transition hover:scale-105 active:scale-95 disabled:opacity-50 flex items-center gap-2"
    >
      {loading ? (
        <span className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></span>
      ) : (
        <span>✨</span>
      )}
      Upgrade to Premium
    </button>
  );
};

export default UpgradeButton;

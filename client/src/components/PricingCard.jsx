// src/components/PricingCard.jsx
import React from 'react';
import { paymentService } from '../services/payments';
import { useApp } from '../context/AppContext';
import { toast } from 'react-toastify';

const PricingCard = ({ planId, onSuccess }) => {
  const { user } = useApp();
  const plan = paymentService.getPlanDetails(planId);

  const handleSubscribe = async () => {
    if (!user) {
      toast.error('Please login to subscribe');
      return;
    }

    await paymentService.initiatePayment(
      user.id,
      user.email,
      planId,
      (data) => {
        console.log('Payment success:', data);
        if (onSuccess) onSuccess(data);
        // Refresh subscription status
        window.location.reload();
      },
      (error) => {
        console.error('Payment failed:', error);
      }
    );
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6 border border-gray-200 hover:shadow-xl transition">
      <h3 className="text-xl font-bold text-gray-900">{plan.name}</h3>
      <div className="mt-4">
        <span className="text-3xl font-bold text-indigo-600">{plan.priceLabel}</span>
      </div>
      {plan.savings && (
        <p className="mt-2 text-sm text-green-600 font-semibold">{plan.savings}</p>
      )}
      <ul className="mt-6 space-y-3">
        {plan.features.map((feature, index) => (
          <li key={index} className="text-sm text-gray-600">{feature}</li>
        ))}
      </ul>
      <button
        onClick={handleSubscribe}
        className="mt-8 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 transition"
      >
        Subscribe Now
      </button>
    </div>
  );
};

export default PricingCard;
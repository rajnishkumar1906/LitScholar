// src/components/PricingCard.jsx
import { useState } from 'react';
import { paymentService } from '../services/payments';
import { useApp } from '../context/AppContext';
import { toast } from 'react-toastify';

const CheckIcon = () => (
  <svg width="15" height="15" viewBox="0 0 15 15" fill="none" style={{ flexShrink: 0, marginTop: 2 }}>
    <circle cx="7.5" cy="7.5" r="7" stroke="rgba(180,130,70,0.45)" strokeWidth="1"/>
    <path d="M4.5 7.5l2 2 4-4" stroke="#c8934a" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
  </svg>
);

const BADGE = { yearly: 'Most Popular', lifetime: 'Best Value' };

const CARD_STYLE = {
  monthly:  { delay: '0ms',    featured: false },
  yearly:   { delay: '110ms',  featured: true  },
  lifetime: { delay: '220ms',  featured: false },
};

export default function PricingCard({ planId, onSuccess }) {
  const { user, checkAuth } = useApp();
  const plan    = paymentService.getPlanDetails(planId);
  const [loading, setLoading] = useState(false);
  const cfg     = CARD_STYLE[planId] || CARD_STYLE.monthly;
  const badge   = BADGE[planId];

  const handleSubscribe = async () => {
    if (!user) { toast.error('Please login to subscribe'); return; }
    setLoading(true);
    await paymentService.initiatePayment(
      user.id, user.email, planId,
      async (data) => { setLoading(false); await checkAuth(); if (onSuccess) onSuccess(data); },
      ()         => setLoading(false)
    );
  };

  return (
    <div
      className={`pricing-card${cfg.featured ? ' pricing-card--featured' : ''}`}
      style={{ animationDelay: cfg.delay }}
    >
      {/* inner shimmer border */}
      <div className="pricing-card__border" />

      {badge && <div className="pricing-card__badge">{badge}</div>}

      <div className="pricing-card__top">
        <p className="pricing-card__label">{plan.name}</p>
        <p className="pricing-card__price">{plan.priceLabel}</p>
        {plan.savings && <p className="pricing-card__savings">{plan.savings}</p>}
      </div>

      <div className="pricing-card__rule" />

      <ul className="pricing-card__list">
        {plan.features.map((f, i) => (
          <li key={i} className="pricing-card__item">
            <CheckIcon />
            <span>{f}</span>
          </li>
        ))}
      </ul>

      <button
        onClick={handleSubscribe}
        disabled={loading}
        className={`pricing-card__btn${cfg.featured ? ' pricing-card__btn--featured' : ''}`}
      >
        {loading
          ? <span className="pricing-card__spinner" />
          : <>
              <span>{planId === 'lifetime' ? 'Get Lifetime Access' : 'Get Started'}</span>
              <svg width="15" height="15" viewBox="0 0 15 15" fill="none">
                <path d="M2.5 7.5h10M9 3.5l4 4-4 4" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </>
        }
      </button>
    </div>
  );
}
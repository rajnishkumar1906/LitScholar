// src/pages/Pricing.jsx
import { useNavigate } from 'react-router-dom';
import Navbar from '../components/Navbar';
import Footer from '../components/Footer';
import PricingCard from '../components/PricingCard';

/* ─── Scoped styles ────────────────────────────────────────────────────── */
const css = `
  /* Page fade-in */
  @keyframes pricingFadeUp {
    from { opacity: 0; transform: translateY(28px); }
    to   { opacity: 1; transform: translateY(0);    }
  }

  /* Card entrance */
  @keyframes cardRise {
    from { opacity: 0; transform: translateY(36px) scale(0.97); }
    to   { opacity: 1; transform: translateY(0)    scale(1);    }
  }

  /* Shimmer sweep on featured card */
  @keyframes shimmer {
    0%   { background-position: -200% center; }
    100% { background-position:  200% center; }
  }

  /* Spinner */
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Hero ── */
  .pricing-hero {
    animation: pricingFadeUp 0.65s cubic-bezier(.22,1,.36,1) both;
    text-align: center;
    padding: 56px 16px 40px;
  }
  .pricing-hero__eyebrow {
    display: inline-block;
    font-family: 'Georgia', serif;
    font-size: 11px;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c8934a;
    background: rgba(200,147,74,0.12);
    border: 1px solid rgba(200,147,74,0.25);
    border-radius: 999px;
    padding: 4px 16px;
    margin-bottom: 20px;
    backdrop-filter: blur(6px);
  }
  .pricing-hero__title {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: clamp(2rem, 5vw, 3.2rem);
    font-weight: 700;
    color: #2c1a0e;
    line-height: 1.15;
    margin: 0 0 14px;
    text-shadow: 0 2px 20px rgba(255,255,255,0.6);
  }
  .pricing-hero__title em {
    font-style: italic;
    color: #040200;
  }
  .pricing-hero__sub {
    font-size: 1.5rem;
    color: rgba(255,255,255);
    max-width: 440px;
    margin: 0 auto;
    line-height: 1.65;
  }

  /* ── Grid ── */
  .pricing-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(270px, 1fr));
    gap: 20px;
    max-width: 980px;
    margin: 0 auto;
    padding: 0 16px 64px;
    align-items: start;
  }
  @media (min-width: 860px) {
    .pricing-grid { grid-template-columns: repeat(3, 1fr); align-items: stretch; }
  }

  /* ── Card base ── */
  .pricing-card {
    position: relative;
    border-radius: 20px;
    padding: 30px 26px 26px;
    background: rgba(255, 248, 238, 0.38);
    backdrop-filter: blur(18px) saturate(1.3);
    -webkit-backdrop-filter: blur(18px) saturate(1.3);
    border: 1px solid rgba(200,147,74,0.22);
    box-shadow:
      0 4px 24px rgba(120,70,20,0.08),
      0 1px 2px  rgba(255,255,255,0.55) inset;
    display: flex;
    flex-direction: column;
    gap: 0;
    animation: cardRise 0.6s cubic-bezier(.22,1,.36,1) both;
    transition: transform 0.25s ease, box-shadow 0.25s ease;
    overflow: hidden;
  }
  .pricing-card:hover {
    transform: translateY(-4px);
    box-shadow:
      0 12px 36px rgba(120,70,20,0.14),
      0 1px 2px rgba(255,255,255,0.6) inset;
  }

  /* ── Featured card (yearly) ── */
  .pricing-card--featured {
    background: rgba(255, 245, 225, 0.55);
    border: 1px solid rgba(200,147,74,0.5);
    box-shadow:
      0 8px 40px rgba(160,100,30,0.18),
      0 0 0 1px rgba(200,147,74,0.15),
      0 1px 2px rgba(255,255,255,0.7) inset;
    transform: translateY(-6px) scale(1.015);
  }
  .pricing-card--featured:hover {
    transform: translateY(-10px) scale(1.015);
    box-shadow:
      0 20px 50px rgba(160,100,30,0.22),
      0 0 0 1px rgba(200,147,74,0.2),
      0 1px 2px rgba(255,255,255,0.7) inset;
  }

  /* ── Shimmer border on featured ── */
  .pricing-card__border {
    display: none;
  }
  .pricing-card--featured .pricing-card__border {
    display: block;
    position: absolute;
    inset: 0;
    border-radius: 20px;
    background: linear-gradient(
      105deg,
      transparent 20%,
      rgba(200,147,74,0.18) 40%,
      rgba(255,220,130,0.22) 50%,
      rgba(200,147,74,0.18) 60%,
      transparent 80%
    );
    background-size: 200% 100%;
    animation: shimmer 3.5s linear infinite;
    pointer-events: none;
    z-index: 0;
  }

  /* ── Badge ── */
  .pricing-card__badge {
    position: absolute;
    top: -1px;
    left: 50%;
    transform: translateX(-50%);
    font-family: 'Georgia', serif;
    font-size: 10px;
    font-style: italic;
    letter-spacing: 0.08em;
    color: #fff8ee;
    background: linear-gradient(90deg, #b8711a, #d4923a, #b8711a);
    border-radius: 0 0 10px 10px;
    padding: 4px 18px 5px;
    white-space: nowrap;
    box-shadow: 0 2px 8px rgba(160,90,20,0.35);
    z-index: 2;
  }

  /* ── Top section ── */
  .pricing-card__top {
    position: relative;
    z-index: 1;
    padding-top: 10px;
    margin-bottom: 18px;
  }
  .pricing-card__label {
    font-size: 11px;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: rgba(120,70,20,0.65);
    font-family: 'Georgia', serif;
    margin: 0 0 10px;
  }
  .pricing-card__price {
    font-family: 'Georgia', 'Times New Roman', serif;
    font-size: 2rem;
    font-weight: 700;
    color: #2c1a0e;
    line-height: 1;
    margin: 0 0 6px;
  }
  .pricing-card--featured .pricing-card__price { color: #8a4a10; }
  .pricing-card__savings {
    font-size: 11.5px;
    color: #7a5c20;
    background: rgba(200,147,74,0.15);
    border: 1px solid rgba(200,147,74,0.25);
    border-radius: 999px;
    padding: 2px 12px;
    display: inline-block;
    font-family: 'Georgia', serif;
    font-style: italic;
  }

  /* ── Divider ── */
  .pricing-card__rule {
    height: 1px;
    background: linear-gradient(90deg, transparent, rgba(200,147,74,0.3), transparent);
    margin: 0 0 18px;
    position: relative;
    z-index: 1;
  }

  /* ── Feature list ── */
  .pricing-card__list {
    list-style: none;
    margin: 0 0 24px;
    padding: 0;
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex-grow: 1;
    position: relative;
    z-index: 1;
  }
  .pricing-card__item {
    display: flex;
    align-items: flex-start;
    gap: 9px;
    font-size: 13px;
    color: rgba(44,26,14,0.75);
    line-height: 1.45;
  }

  /* ── CTA button ── */
  .pricing-card__btn {
    position: relative;
    z-index: 1;
    width: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 8px;
    padding: 12px 20px;
    border-radius: 12px;
    border: 1px solid rgba(200,147,74,0.35);
    background: rgba(255,248,238,0.5);
    backdrop-filter: blur(8px);
    color: #7a4a10;
    font-size: 13.5px;
    font-weight: 600;
    font-family: 'Georgia', serif;
    cursor: pointer;
    transition: all 0.2s ease;
    box-shadow: 0 2px 8px rgba(120,70,20,0.08);
  }
  .pricing-card__btn:hover:not(:disabled) {
    background: rgba(200,147,74,0.18);
    border-color: rgba(200,147,74,0.6);
    color: #5a3208;
    box-shadow: 0 4px 16px rgba(120,70,20,0.15);
    transform: translateY(-1px);
  }
  .pricing-card__btn--featured {
    background: linear-gradient(135deg, #b8711a 0%, #d4923a 50%, #b8711a 100%);
    border-color: transparent;
    color: #fff8ee;
    box-shadow: 0 4px 20px rgba(160,90,20,0.35);
  }
  .pricing-card__btn--featured:hover:not(:disabled) {
    background: linear-gradient(135deg, #a86015 0%, #c4822a 50%, #a86015 100%);
    box-shadow: 0 8px 28px rgba(160,90,20,0.45);
    transform: translateY(-2px);
    color: #fff8ee;
  }
  .pricing-card__btn:disabled { opacity: 0.6; cursor: not-allowed; transform: none; }

  /* ── Spinner ── */
  .pricing-card__spinner {
    width: 18px;
    height: 18px;
    border: 2px solid currentColor;
    border-top-color: transparent;
    border-radius: 50%;
    animation: spin 0.7s linear infinite;
    display: inline-block;
  }

  /* ── Footer note ── */
  .pricing-footer-note {
    text-align: center;
    font-family: 'Georgia', serif;
    font-style: italic;
    font-size: 12px;
    color: rgba(44,26,14,0.45);
    padding-bottom: 32px;
    animation: pricingFadeUp 0.8s 0.4s cubic-bezier(.22,1,.36,1) both;
  }
  .pricing-footer-note a {
    color: #9a6020;
    text-decoration: underline;
    text-underline-offset: 3px;
    cursor: pointer;
  }
`;

export default function Pricing() {
  const navigate = useNavigate();

  return (
    <>
      <style dangerouslySetInnerHTML={{ __html: css }} />

      <div className="min-h-screen flex flex-col">
        <Navbar />

        <main className="flex-grow">
          {/* Hero */}
          <div className="pricing-hero">
            <span className="pricing-hero__eyebrow">✦ LitScholar Premium ✦</span>
            <h1 className="pricing-hero__title">
              Read deeper.<br /><em>Think sharper.</em>
            </h1>
            <p className="pricing-hero__sub">
              One plan unlocks everything — AI summaries, curated recommendations,
              and a reading companion that grows with you.
            </p>
          </div>

          {/* Cards */}
          <div className="pricing-grid">
            <PricingCard planId="monthly"  onSuccess={() => navigate('/dashboard')} />
            <PricingCard planId="yearly"   onSuccess={() => navigate('/dashboard')} />
            <PricingCard planId="lifetime" onSuccess={() => navigate('/dashboard')} />
          </div>

          {/* Footer note */}
          <p className="pricing-footer-note">
            Secure payments via Razorpay &nbsp;·&nbsp; Cancel anytime &nbsp;·&nbsp;{' '}
            <a onClick={() => navigate('/dashboard')}>Back to Dashboard</a>
          </p>
        </main>

        <Footer />
      </div>
    </>
  );
}
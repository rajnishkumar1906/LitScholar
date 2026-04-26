import { useEffect, useState } from 'react';
import LitScholarLogo from './LitScholarLogo';

/** Minimum time splash stays fully visible before fade-out (then routes show). */
const DISPLAY_MS = 4000;
const FADE_OUT_MS = 4000;

/**
 * Full-viewport splash: glassmorphism card, root fade-in/out, motion across edges and corners.
 */
export default function SplashScreen({ onDismiss }) {
  const [phase, setPhase] = useState('in');

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('out'), DISPLAY_MS);
    const t2 = setTimeout(() => onDismiss?.(), DISPLAY_MS + FADE_OUT_MS);
    return () => {
      clearTimeout(t1);
      clearTimeout(t2);
    };
  }, [onDismiss]);

  return (
    <div
      className={`splash-screen-root ${phase === 'out' ? 'splash-screen-root--exit' : ''}`}
      role="status"
      aria-live="polite"
      aria-label="Loading LitScholar"
    >
      {/* Full-screen layers (fade handled on root + this overlay for blur/saturation) */}
      <div className="splash-backdrop-stack" aria-hidden />

      <div
        className="splash-bg-drift absolute inset-0 bg-cover bg-center bg-no-repeat"
        style={{ backgroundImage: "url('/bookbuddy-bg.png')" }}
      />
      <div className="splash-vignette absolute inset-0" />
      <div className="absolute inset-0 bg-gradient-to-b from-amber-50/15 via-transparent to-amber-950/20" aria-hidden />

      {/* Whole-frame: horizontal light bands */}
      <div className="splash-band splash-band-top" aria-hidden />
      <div className="splash-band splash-band-bottom" aria-hidden />

      {/* Whole-frame: diagonal sweep across viewport */}
      <div className="splash-diagonal-sweep" aria-hidden />

      {/* Whole-frame: floating orbs (not only center) */}
      <div className="pointer-events-none absolute inset-0 overflow-hidden" aria-hidden>
        <div className="splash-orb splash-orb-a" />
        <div className="splash-orb splash-orb-b" />
        <div className="splash-orb splash-orb-c" />
        <div className="splash-orb splash-orb-d" />
      </div>

      {/* Corner glass chips — motion from corners inward */}
      <div className="splash-corner-chip splash-corner-tl" aria-hidden />
      <div className="splash-corner-chip splash-corner-tr" aria-hidden />
      <div className="splash-corner-chip splash-corner-bl" aria-hidden />
      <div className="splash-corner-chip splash-corner-br" aria-hidden />

      {/* Subtle grid */}
      <div
        className="pointer-events-none absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage:
            'linear-gradient(rgba(120,53,15,0.35) 1px, transparent 1px), linear-gradient(90deg, rgba(120,53,15,0.35) 1px, transparent 1px)',
          backgroundSize: '56px 56px',
        }}
        aria-hidden
      />

      {/* Bottom full-bleed glass strip */}
      <div className="splash-lower-glass" aria-hidden />

      {/* Card: glassmorphism — centered but entrance from below + scale */}
      <div className="splash-card-outer pointer-events-none flex min-h-full w-full items-center justify-center px-4 py-10 sm:px-8">
        <div className="splash-card-shell pointer-events-auto w-full max-w-lg">
          <div className="splash-ring-glow absolute -inset-[1px] rounded-[2rem] opacity-80 blur-2xl" aria-hidden />

          <div className="splash-card-glass relative overflow-hidden rounded-[1.85rem] px-8 py-10 sm:px-12 sm:py-12">
            <div className="splash-card-inner-highlight absolute inset-0 rounded-[1.85rem]" aria-hidden />
            <div className="splash-shine absolute inset-0 overflow-hidden rounded-[1.85rem]" aria-hidden />

            <div className="relative flex flex-col items-center text-center">
              <div className="splash-logo-stage mb-8 flex justify-center">
                <div className="splash-logo-glow relative">
                  <LitScholarLogo className="relative z-10 h-28 w-28 sm:h-32 sm:w-32" animated />
                </div>
              </div>

              <h1 className="splash-title-shimmer mb-3 text-4xl font-bold tracking-tight sm:text-5xl md:text-6xl">
                LitScholar
              </h1>

              <p className="splash-tagline mb-10 max-w-sm text-sm font-medium leading-relaxed text-amber-950/75 sm:text-base">
                Your AI librarian — discover, read, and explore with intelligence that understands books.
              </p>

              <div className="splash-progress-wrap mb-4 w-full max-w-xs">
                <div className="splash-progress-track relative h-2 overflow-hidden rounded-full">
                  <div className="splash-progress-fill absolute inset-y-0 left-0 rounded-full" />
                  <div className="splash-progress-glow absolute inset-y-0 left-0 w-1/3 rounded-full opacity-70 blur-sm" />
                </div>
              </div>

              <p className="splash-hint flex items-center justify-center gap-1 text-xs font-medium uppercase tracking-[0.2em] text-amber-900/55">
                <span>Opening your library</span>
                <span className="inline-flex w-6 justify-start" aria-hidden>
                  <span className="splash-dot">.</span>
                  <span className="splash-dot">.</span>
                  <span className="splash-dot">.</span>
                </span>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

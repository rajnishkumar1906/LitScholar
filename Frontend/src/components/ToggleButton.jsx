import React, { useState, useEffect, useMemo } from 'react';

// Static configuration for dots (no need to generate on every render)
const DOT_CONFIG = {
  outerCount: 8,
  innerCount: 6,
  outerRadius: 28,
  innerRadius: 18,
  baseDelay: 0.1,
};

const ToggleButton = ({ showSearchSection, onToggle }) => {
  const [rotationAngle, setRotationAngle] = useState(0);

  // Generate outer dots once
  const outerDots = useMemo(() => 
    Array.from({ length: DOT_CONFIG.outerCount }, (_, i) => ({
      id: i,
      angle: (i * 360) / DOT_CONFIG.outerCount,
      delay: i * DOT_CONFIG.baseDelay,
    })), []
  );

  // Generate inner dots once
  const innerDots = useMemo(() => 
    Array.from({ length: DOT_CONFIG.innerCount }, (_, i) => ({
      id: i,
      angle: (i * 360) / DOT_CONFIG.innerCount + 15, // offset
      delay: i * DOT_CONFIG.baseDelay + 0.2,
    })), []
  );

  // Smooth rotation using CSS transition (simpler and GPU-accelerated)
  useEffect(() => {
    // Trigger rotation by updating a CSS variable
    const targetAngle = showSearchSection ? 360 : 0;
    setRotationAngle(targetAngle);
  }, [showSearchSection]);

  return (
    <button
      onClick={onToggle}
      className="fixed bottom-8 right-8 w-20 h-20 group focus:outline-none focus:ring-4 focus:ring-amber-300 rounded-full z-50"
      aria-label={showSearchSection ? "Show recommendations" : "Search for books"}
    >
      <div className="relative w-full h-full flex items-center justify-center">
        {/* Animated background ping */}
        <div className="absolute inset-0 rounded-full bg-amber-400 animate-ping opacity-20" />

        {/* Outer rotating ring with dots */}
        <div
          className="absolute inset-0 rounded-full transition-transform duration-1000 ease-out"
          style={{ transform: `rotate(${rotationAngle}deg)` }}
        >
          {outerDots.map((dot) => (
            <div
              key={dot.id}
              className="absolute w-1.5 h-1.5"
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${dot.angle}deg) translateY(-${DOT_CONFIG.outerRadius}px) translateX(-50%)`,
              }}
            >
              <div
                className="w-1.5 h-1.5 rounded-full bg-amber-300 animate-pulse"
                style={{
                  animationDelay: `${dot.delay}s`,
                  boxShadow: '0 0 10px rgba(251, 191, 36, 0.8)',
                }}
              />
            </div>
          ))}
        </div>

        {/* Inner ring rotating opposite direction */}
        <div
          className="absolute inset-0 rounded-full transition-transform duration-1000 ease-out"
          style={{ transform: `rotate(${-rotationAngle * 0.5}deg)` }}
        >
          {innerDots.map((dot) => (
            <div
              key={`inner-${dot.id}`}
              className="absolute w-1 h-1"
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${dot.angle}deg) translateY(-${DOT_CONFIG.innerRadius}px) translateX(-50%)`,
              }}
            >
              <div
                className="w-1 h-1 rounded-full bg-amber-400/70"
                style={{ animationDelay: `${dot.delay}s` }}
              />
            </div>
          ))}
        </div>

        {/* Gradient ring with optional spin animation (can be removed if not needed) */}
        <div className="absolute inset-0 rounded-full bg-gradient-to-r from-amber-300 via-amber-500 to-amber-700 p-[3px]">
          <div className="w-full h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-700" />
        </div>

        {/* Decorative borders (static now) */}
        <div className="absolute inset-0 rounded-full border-2 border-white/40" />
        <div className="absolute inset-0 rounded-full border border-dashed border-white/30" />

        {/* Floating particles - kept as is */}
        <div className="absolute -top-2 -right-2 w-3 h-3 bg-amber-300 rounded-full animate-ping opacity-75" />
        <div className="absolute -bottom-1 -left-1 w-2 h-2 bg-amber-400 rounded-full animate-ping delay-150 opacity-60" />
        <div className="absolute top-1/2 -right-3 w-1.5 h-1.5 bg-amber-200 rounded-full animate-ping delay-300 opacity-50" />

        {/* Center icon container */}
        <div
          className="relative w-14 h-14 bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center transition-all duration-700 group-hover:bg-white/20 group-hover:shadow-2xl group-hover:shadow-amber-500/50 border border-white/30 overflow-hidden"
        >
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent -translate-x-full group-hover:translate-x-full transition-transform duration-1000" />
          <div className="relative transition-transform duration-500 group-hover:scale-125">
            {showSearchSection ? (
              <svg className="w-8 h-8 text-white filter drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            ) : (
              <svg className="w-8 h-8 text-white filter drop-shadow-lg" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
            )}
          </div>
        </div>

        {/* Glow effect */}
        <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-amber-400 blur-xl -z-10" />

        {/* Tooltip */}
        <div className="absolute -top-16 right-0 bg-gradient-to-r from-gray-900 to-gray-800 text-white text-sm px-5 py-2.5 rounded-2xl opacity-0 group-hover:opacity-100 transition-all duration-300 whitespace-nowrap shadow-2xl backdrop-blur-sm border border-amber-500/50 translate-y-2 group-hover:translate-y-0 pointer-events-none">
          <div className="absolute -bottom-1 right-6 w-2 h-2 bg-gray-900 border-r border-b border-amber-500/30 transform rotate-45" />
          <span className="font-medium">
            {showSearchSection ? '📚 Show Recommendations' : '🔍 Search for Books'}
          </span>
        </div>

        {/* Energy waves */}
        <div className="absolute inset-0 rounded-full border-2 border-amber-400/0 group-hover:border-amber-400/30 transition-all duration-500 scale-110 group-hover:scale-125 opacity-0 group-hover:opacity-100" />
        <div className="absolute inset-0 rounded-full border border-amber-400/0 group-hover:border-amber-400/20 transition-all duration-700 scale-125 group-hover:scale-150 opacity-0 group-hover:opacity-100" />
      </div>
    </button>
  );
};

export default ToggleButton;
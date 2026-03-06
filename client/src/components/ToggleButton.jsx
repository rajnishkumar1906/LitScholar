import React, { useEffect, useState } from 'react';

const ToggleButton = ({ showSearchSection, onToggle, isRotating }) => {
  const [dots, setDots] = useState([]);
  const [rotationAngle, setRotationAngle] = useState(0);

  // Create 8 dots around the button
  useEffect(() => {
    const newDots = [];
    const count = 8;
    for (let i = 0; i < count; i++) {
      const angle = (i * 360) / count;
      newDots.push({
        id: i,
        angle: angle,
        delay: i * 0.1,
      });
    }
    setDots(newDots);
  }, []);

  // Animate rotation based on showSearchSection
  useEffect(() => {
    let animationFrame;
    const startTime = Date.now();
    const startAngle = rotationAngle;
    const targetAngle = showSearchSection ? 360 : 0;
    const duration = 1000; // 1 second animation

    const animate = () => {
      const now = Date.now();
      const elapsed = now - startTime;
      const progress = Math.min(elapsed / duration, 1);
      
      // Easing function for smooth animation
      const easeProgress = 1 - Math.pow(1 - progress, 3);
      const newAngle = startAngle + (targetAngle - startAngle) * easeProgress;
      
      setRotationAngle(newAngle % 360);

      if (progress < 1) {
        animationFrame = requestAnimationFrame(animate);
      }
    };

    animationFrame = requestAnimationFrame(animate);
    return () => cancelAnimationFrame(animationFrame);
  }, [showSearchSection]);

  return (
    <button
      onClick={onToggle}
      className="fixed bottom-8 right-8 w-20 h-20 group focus:outline-none focus:ring-4 focus:ring-amber-300 rounded-full z-50"
    >
      <div className="relative w-full h-full flex items-center justify-center">
        {/* Animated background rings */}
        <div className="absolute inset-0 rounded-full bg-amber-400 animate-ping opacity-20"></div>
        
        {/* Rotating dots ring */}
        <div 
          className="absolute inset-0 rounded-full"
          style={{
            transform: `rotate(${rotationAngle}deg)`,
            transition: 'transform 0.1s linear'
          }}
        >
          {dots.map((dot) => (
            <div
              key={dot.id}
              className="absolute w-1.5 h-1.5"
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${dot.angle}deg) translateY(-28px) translateX(-50%)`,
              }}
            >
              <div 
                className={`w-1.5 h-1.5 rounded-full bg-amber-300 animate-pulse`}
                style={{
                  animationDelay: `${dot.delay}s`,
                  boxShadow: '0 0 10px rgba(251, 191, 36, 0.8)'
                }}
              />
            </div>
          ))}
        </div>

        {/* Second ring of dots (smaller) */}
        <div 
          className="absolute inset-0 rounded-full"
          style={{
            transform: `rotate(${-rotationAngle * 0.5}deg)`,
            transition: 'transform 0.1s linear'
          }}
        >
          {dots.slice(0, 6).map((dot, index) => (
            <div
              key={`inner-${index}`}
              className="absolute w-1 h-1"
              style={{
                left: '50%',
                top: '50%',
                transform: `rotate(${dot.angle + 15}deg) translateY(-18px) translateX(-50%)`,
              }}
            >
              <div 
                className="w-1 h-1 rounded-full bg-amber-400/70"
                style={{
                  animationDelay: `${dot.delay + 0.2}s`,
                }}
              />
            </div>
          ))}
        </div>

        {/* Main gradient ring */}
        <div className={`absolute inset-0 rounded-full bg-gradient-to-r from-amber-300 via-amber-500 to-amber-700 ${isRotating ? (showSearchSection ? 'animate-spin-reverse' : 'animate-spin') : ''}`}
          style={{ padding: '3px' }}>
          <div className="w-full h-full rounded-full bg-gradient-to-r from-amber-600 to-amber-700"></div>
        </div>
        
        {/* Decorative borders */}
        <div className={`absolute inset-0 rounded-full border-2 border-white/40 ${isRotating ? (showSearchSection ? 'animate-spin-reverse' : 'animate-spin') : ''}`}></div>
        <div className={`absolute inset-0 rounded-full border border-dashed border-white/30 ${isRotating ? (showSearchSection ? 'animate-spin-reverse' : 'animate-spin') : ''}`}
          style={{ animationDuration: '3s' }}></div>

        {/* Floating particles */}
        <div className="absolute -top-2 -right-2 w-3 h-3 bg-amber-300 rounded-full animate-ping opacity-75"></div>
        <div className="absolute -bottom-1 -left-1 w-2 h-2 bg-amber-400 rounded-full animate-ping delay-150 opacity-60"></div>
        <div className="absolute top-1/2 -right-3 w-1.5 h-1.5 bg-amber-200 rounded-full animate-ping delay-300 opacity-50"></div>

        {/* Center icon container */}
        <div className={`relative w-14 h-14 bg-white/10 backdrop-blur-sm rounded-full flex items-center justify-center transition-all duration-700 
          ${isRotating ? 'scale-90 rotate-180' : 'scale-100'} 
          group-hover:bg-white/20 group-hover:shadow-2xl group-hover:shadow-amber-500/50
          border border-white/30 overflow-hidden`}>
          
          {/* Shimmer effect */}
          <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent 
            -translate-x-full group-hover:translate-x-full transition-transform duration-1000"></div>
          
          {/* Icon with scale animation */}
          <div className="relative transition-all duration-500 ease-in-out transform group-hover:scale-125">
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
        <div className="absolute inset-0 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300 bg-amber-400 blur-xl -z-10"></div>

        {/* Tooltip */}
        <div className="absolute -top-16 right-0 bg-gradient-to-r from-gray-900 to-gray-800 text-white text-sm px-5 py-2.5 rounded-2xl 
          opacity-0 group-hover:opacity-100 transition-all duration-300 
          whitespace-nowrap shadow-2xl backdrop-blur-sm border border-amber-500/50
          translate-y-2 group-hover:translate-y-0 pointer-events-none">
          <div className="absolute -bottom-1 right-6 w-2 h-2 bg-gray-900 border-r border-b border-amber-500/30 transform rotate-45"></div>
          <span className="font-medium">
            {showSearchSection ? '📚 Show Recommendations' : '🔍 Search for Books'}
          </span>
        </div>

        {/* Energy waves */}
        <div className="absolute inset-0 rounded-full border-2 border-amber-400/0 group-hover:border-amber-400/30 
          transition-all duration-500 scale-110 group-hover:scale-125 opacity-0 group-hover:opacity-100"></div>
        <div className="absolute inset-0 rounded-full border border-amber-400/0 group-hover:border-amber-400/20 
          transition-all duration-700 scale-125 group-hover:scale-150 opacity-0 group-hover:opacity-100"></div>
      </div>
    </button>
  );
};

export default ToggleButton;
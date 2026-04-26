import React from 'react';

const LitScholarLogo = ({ className = "w-10 h-10", animated = true }) => {
  return (
    <svg 
      viewBox="0 0 100 100" 
      fill="none" 
      xmlns="http://www.w3.org/2000/svg"
      className={className}
    >
      {/* Animated glow effect */}
      {animated && (
        <circle 
          cx="50" 
          cy="50" 
          r="45" 
          className="animate-ping opacity-20"
          fill="url(#gradGlow)"
        />
      )}
      
      {/* Book base */}
      <path 
        d="M20 25 L80 25 L80 75 L20 75 Z" 
        fill="url(#gradBook)" 
        stroke="url(#gradStroke)" 
        strokeWidth="3" 
        rx="8"
        className="drop-shadow-lg"
      />
      
      {/* Book spine */}
      <rect 
        x="45" 
        y="25" 
        width="10" 
        height="50" 
        fill="url(#gradSpine)" 
        rx="2"
      />
      
      {/* Book pages lines */}
      <path d="M22 28 L78 28" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 35 L78 35" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 42 L78 42" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 49 L78 49" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 56 L78 56" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 63 L78 63" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      <path d="M22 70 L78 70" stroke="white" strokeWidth="1.5" strokeDasharray="4 4" opacity="0.8"/>
      
      {/* Scholar's cap/AI symbol */}
      <circle 
        cx="70" 
        cy="35" 
        r="12" 
        fill="white" 
        fillOpacity="0.95" 
        stroke="url(#gradStroke)" 
        strokeWidth="2"
      />
      <path 
        d="M70 30 L70 40 M65 35 L75 35" 
        stroke="url(#gradStroke)" 
        strokeWidth="2.5" 
        strokeLinecap="round"
      />
      <circle cx="70" cy="35" r="4" fill="url(#gradStroke)"/>
      
      {/* Reading glasses */}
      <circle cx="35" cy="45" r="8" fill="white" fillOpacity="0.9" stroke="url(#gradStroke)" strokeWidth="2"/>
      <circle cx="55" cy="45" r="8" fill="white" fillOpacity="0.9" stroke="url(#gradStroke)" strokeWidth="2"/>
      <path d="M43 45 L47 45" stroke="url(#gradStroke)" strokeWidth="2.5"/>
      
      {/* Small star for scholarly excellence */}
      <path 
        d="M80 65 L82 69 L86 70 L82 71 L80 75 L78 71 L74 70 L78 69 L80 65" 
        fill="white" 
        opacity="0.9"
        className={animated ? "animate-pulse" : ""}
      />
      
      {/* Gradients - Brown tones */}
      <defs>
        <linearGradient id="gradBook" x1="20" y1="25" x2="80" y2="75" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B5A2B">
            {animated && (
              <animate 
                attributeName="stop-color" 
                values="#8B5A2B;#A0522D;#8B4513;#8B5A2B" 
                dur="8s" 
                repeatCount="indefinite" 
                fill="freeze"
              />
            )}
          </stop>
          <stop offset="0.5" stopColor="#A0522D">
            {animated && (
              <animate 
                attributeName="stop-color" 
                values="#A0522D;#8B4513;#8B5A2B;#A0522D" 
                dur="8s" 
                repeatCount="indefinite" 
                fill="freeze"
              />
            )}
          </stop>
          <stop offset="1" stopColor="#8B4513">
            {animated && (
              <animate 
                attributeName="stop-color" 
                values="#8B4513;#8B5A2B;#A0522D;#8B4513" 
                dur="8s" 
                repeatCount="indefinite" 
                fill="freeze"
              />
            )}
          </stop>
        </linearGradient>
        
        <linearGradient id="gradStroke" x1="20" y1="25" x2="80" y2="75" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B5A2B"/>
          <stop offset="1" stopColor="#5D3A1A"/>
        </linearGradient>
        
        <linearGradient id="gradSpine" x1="45" y1="25" x2="55" y2="75" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B4513"/>
          <stop offset="1" stopColor="#5D3A1A"/>
        </linearGradient>
        
        <radialGradient id="gradGlow" cx="50" cy="50" r="50" gradientUnits="userSpaceOnUse">
          <stop stopColor="#8B5A2B"/>
          <stop offset="1" stopColor="#5D3A1A" stopOpacity="0"/>
        </radialGradient>
      </defs>
    </svg>
  );
};

export default LitScholarLogo;
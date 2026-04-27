import React from 'react';

export default function ProgressRing({ current, max, size = 200, strokeWidth = 16 }) {
  const radius = (size - strokeWidth) / 2;
  const circumference = radius * 2 * Math.PI;
  
  // Cap progress at 100% so it doesn't spin backwards
  const percent = Math.min((current / max) * 100, 100);
  const strokeDashoffset = circumference - (percent / 100) * circumference;

  return (
    <div style={styles.container}>
      <svg
        width={size}
        height={size}
        style={{ transform: 'rotate(-90deg)' }}
      >
        <defs>
          <linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="var(--primary-amber)" />
            <stop offset="100%" stopColor="var(--primary-coral)" />
          </linearGradient>
        </defs>

        {/* Background Track Circle */}
        <circle
          stroke="var(--glass-border)"
          fill="transparent"
          strokeWidth={strokeWidth}
          r={radius}
          cx={size / 2}
          cy={size / 2}
        />

        {/* Dynamic Interactive Foreground Circle */}
        <circle
          stroke="url(#ringGradient)"
          fill="transparent"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          r={radius}
          cx={size / 2}
          cy={size / 2}
          style={{ transition: 'stroke-dashoffset 0.8s cubic-bezier(0.4, 0, 0.2, 1)' }}
        />
      </svg>
      
      {/* Central Metrics Text */}
      <div style={styles.innerContent}>
        <span style={styles.current}>{current}</span>
        <span style={styles.divider}>/</span>
        <span style={styles.max}>{max}</span>
        <span style={styles.unit}>kcal</span>
      </div>
    </div>
  );
}

const styles = {
  container: {
    position: 'relative',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    margin: '20px 0'
  },
  innerContent: {
    position: 'absolute',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    transform: 'translateY(-2px)' // visual center offset
  },
  current: {
    fontSize: '2.5rem',
    fontWeight: '700',
    color: 'var(--text-h)',
    lineHeight: '1',
    fontFamily: 'var(--font-heading)'
  },
  divider: {
    fontSize: '1rem',
    opacity: 0.5,
    margin: '2px 0'
  },
  max: {
    fontSize: '1.2rem',
    opacity: 0.8,
    fontWeight: '600'
  },
  unit: {
    fontSize: '0.8rem',
    opacity: 0.6,
    marginTop: '4px',
    color: 'var(--primary-coral)',
    fontWeight: 'bold'
  }
};

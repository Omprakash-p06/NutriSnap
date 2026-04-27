import { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Info, AlertTriangle, CheckCircle2, ChevronRight, ChevronLeft } from 'lucide-react';
import SpotlightCard from '../common/SpotlightCard';

/**
 * InsightCards
 * Displays personalized AI-driven health tips and coaching.
 */
export default function InsightCards({ userEmail }) {
  const [insights, setInsights] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);

  useEffect(() => {
    if (userEmail) {
      fetchInsights();
    }
  }, [userEmail]);

  const fetchInsights = async () => {
    try {
      const res = await fetch(`/api/insights?email=${userEmail}`);
      const data = await res.json();
      setInsights(data);
    } catch (err) {
      console.error("Failed to fetch insights:", err);
    }
  };

  if (!insights || insights.length === 0) return null;

  const current = insights[currentIndex];

  const getTypeIcon = (type) => {
    switch(type) {
      case 'success': return <CheckCircle2 size={24} color="#3ECFA0" />;
      case 'warning': return <AlertTriangle size={24} color="#FFB347" />;
      default: return <Info size={24} color="#3E90CF" />;
    }
  };

  return (
    <div className="insights-container" style={{ margin: '20px 0', position: 'relative' }}>
      <AnimatePresence mode="wait">
        <motion.div
          key={currentIndex}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.4 }}
        >
          <SpotlightCard 
            className="glass-card insight-card" 
            glowColor={current.type === 'warning' ? 'rgba(255, 179, 71, 0.1)' : 'rgba(62, 207, 160, 0.1)'}
            style={{ padding: '24px', display: 'flex', gap: '20px', alignItems: 'center' }}
          >
            <div className="insight-icon-ring" style={{ 
              width: '50px', 
              height: '50px', 
              borderRadius: '50%', 
              background: 'rgba(255,255,255,0.05)', 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'center',
              flexShrink: 0
            }}>
              {getTypeIcon(current.type)}
            </div>

            <div style={{ flex: 1 }}>
              <h4 style={{ margin: '0 0 4px 0', fontSize: '1.1rem', fontWeight: 700 }}>{current.title}</h4>
              <p style={{ margin: 0, fontSize: '0.9rem', opacity: 0.8, lineHeight: 1.4 }}>{current.message}</p>
            </div>

            <div style={{ display: 'flex', gap: '8px' }}>
              <button 
                onClick={() => setCurrentIndex(prev => (prev === 0 ? insights.length - 1 : prev - 1))}
                style={{ background: 'transparent', border: 'none', color: 'var(--text)', cursor: 'pointer', opacity: 0.5 }}
              >
                <ChevronLeft size={20} />
              </button>
              <button 
                onClick={() => setCurrentIndex(prev => (prev === insights.length - 1 ? 0 : prev + 1))}
                style={{ background: 'transparent', border: 'none', color: 'var(--text)', cursor: 'pointer', opacity: 0.5 }}
              >
                <ChevronRight size={20} />
              </button>
            </div>
          </SpotlightCard>
        </motion.div>
      </AnimatePresence>
      
      {/* Indicator Dots */}
      <div style={{ display: 'flex', justifyContent: 'center', gap: '6px', marginTop: '10px' }}>
        {insights.map((_, i) => (
          <div 
            key={i} 
            style={{ 
              width: '6px', 
              height: '6px', 
              borderRadius: '50%', 
              background: i === currentIndex ? 'var(--accent-mint)' : 'rgba(255,255,255,0.2)',
              transition: 'background 0.3s ease'
            }} 
          />
        ))}
      </div>
    </div>
  );
}

import { motion } from 'framer-motion';
import SplitText from '../common/SplitText';

/**
 * Hero component for the landing page.
 * Uses SplitText for premium entrance animations.
 */
export default function Hero() {
  return (
    <section className="hero-section">
      <div className="glass-card hero-content">
        <h1 style={{ fontSize: '4rem', margin: '0 0 20px 0', lineHeight: 1.1, fontWeight: 'bold' }}>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            Eat Better,
          </motion.div>
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.2 }}
            className="text-gradient"
          >
            Feel Better
          </motion.div>
        </h1>
        <motion.p 
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 1, duration: 0.8 }}
          style={{ fontSize: '1.2rem', marginBottom: '30px', opacity: 0.8 }}
        >
          AI-powered nutrition tracking made simple
        </motion.p>
      </div>
    </section>
  );
}

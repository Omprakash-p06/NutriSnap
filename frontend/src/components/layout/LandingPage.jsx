import { useState, useEffect, useRef } from "react";
import {
  motion,
  useScroll,
  useTransform,
  AnimatePresence,
} from "framer-motion";
import { useAuth } from "../../context/AuthContext";
import {
  Camera,
  Flame,
  Droplets,
  BarChart3,
  Search,
  Rocket,
  Zap,
  Dumbbell,
  ArrowRight,
} from "lucide-react";
import BorderGlow from "../common/BorderGlow";
import Magnet from "../common/Magnet";
import ModelViewer from "../common/ModelViewer";
import "./LandingPage.css";

/* ─── Data ─────────────────────────────────────────────────── */

const FEATURES = [
  {
    icon: <Camera size={24} />,
    title: "Snap & Track",
    desc: "AI vision identifies your meal instantly from a single photo — calories, protein, carbs, fat in seconds.",
    accent: "#FF6B5A",
    glow: "15 80 70",
    colors: ["#FF6B5A", "#FFB347", "#FF8C69"],
  },
  {
    icon: <Flame size={24} />,
    title: "Streak Engine",
    desc: "Daily streak system keeps you accountable. Build momentum, level up your fitness with XP rewards.",
    accent: "#FFB347",
    glow: "40 90 75",
    colors: ["#FFB347", "#FF6B5A", "#FFD700"],
  },
  {
    icon: <Droplets size={24} />,
    title: "Smart Hydration",
    desc: "Track water intake with one tap. Real-time visual feedback with beautiful wave animations and daily goals.",
    accent: "#3ECFA0",
    glow: "160 80 65",
    colors: ["#3ECFA0", "#38bdf8", "#6ee7b7"],
  },
  {
    icon: <BarChart3 size={24} />,
    title: "Weekly Insights",
    desc: "AI-powered coaching from your weekly data. Know exactly what to eat more or less of every single week.",
    accent: "#6B3FA0",
    glow: "270 80 70",
    colors: ["#6B3FA0", "#9b59b6", "#c084fc"],
  },
];

const FOOD_3D_MODELS = [
  {
    url: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/Avocado/glTF-Binary/Avocado.glb",
    label: "Avocado",
  },
  {
    url: "https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/WaterBottle/glTF-Binary/WaterBottle.glb",
    label: "Hydration",
  },
];

/* ─── Sub-components ────────────────────────────────────────── */

function FeatureCard({ feature, index }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 40 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      transition={{ delay: index * 0.1, duration: 0.5, ease: "easeOut" }}
      className="feature-card-wrapper"
    >
      <BorderGlow
        backgroundColor="rgba(10,8,18,0.92)"
        glowColor={feature.glow}
        colors={feature.colors}
        borderRadius={24}
        glowRadius={35}
        glowIntensity={0.85}
        coneSpread={28}
      >
        <div className="feature-card-inner">
          <div
            className="feature-card-icon"
            style={{ "--accent": feature.accent }}
          >
            {feature.icon}
          </div>
          <h3 className="feature-card-title">{feature.title}</h3>
          <p className="feature-card-desc">{feature.desc}</p>
        </div>
      </BorderGlow>
    </motion.div>
  );
}

function HowStep({ step, title, desc, delay }) {
  return (
    <motion.div
      className="how-step"
      initial={{ opacity: 0, x: -20 }}
      whileInView={{ opacity: 1, x: 0 }}
      viewport={{ once: true }}
      transition={{ delay, duration: 0.5 }}
    >
      <div className="how-step-num">{step}</div>
      <div>
        <h4 className="how-step-title">{title}</h4>
        <p className="how-step-desc">{desc}</p>
      </div>
    </motion.div>
  );
}

/* ─── Main Landing Page ─────────────────────────────────────── */

export default function LandingPage({ onGetStarted }) {
  const { loginAsGuest, isAuthenticated, setViewMode } = useAuth();
  const [activeWord, setActiveWord] = useState(0);
  const heroRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: heroRef,
    offset: ["start start", "end start"],
  });
  const runnerY = useTransform(scrollYProgress, [0, 1], [0, 80]);
  const runnerOpacity = useTransform(scrollYProgress, [0, 0.7], [1, 0]);

  const words = ["STRONGER", "LEANER", "HEALTHIER", "SMARTER"];

  useEffect(() => {
    const timer = setInterval(() => {
      setActiveWord((prev) => (prev + 1) % words.length);
    }, 2000);
    return () => clearInterval(timer);
  }, []);

  const handleGetStarted = () => {
    setViewMode("app");
    if (onGetStarted) onGetStarted();
  };

  return (
    <div className="landing-page">
      {/* ═══════════════════════════════════════
          HERO SECTION
      ═══════════════════════════════════════ */}
      <section className="hero-full" ref={heroRef}>
        {/* Ambient orbs */}
        <div className="hero-orb hero-orb-1" />
        <div className="hero-orb hero-orb-2" />
        <div className="hero-orb hero-orb-3" />

        <div className="hero-layout">
          {/* LEFT: Text */}
          <div className="hero-text-col">
            <motion.div
              initial={{ opacity: 0, y: -20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="hero-badge"
            >
              <span className="hero-badge-dot" />
              AI-POWERED NUTRITION TRACKING
            </motion.div>

            <h1 className="hero-headline">
              <motion.span
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.1 }}
                className="hero-headline-fuel"
              >
                BECOME
              </motion.span>
              <span className="hero-headline-word-wrap">
                <AnimatePresence>
                  <motion.span
                    key={activeWord}
                    initial={{ opacity: 0, y: 20, filter: "blur(10px)" }}
                    animate={{ opacity: 1, y: 0, filter: "blur(0px)" }}
                    exit={{ opacity: 0, y: -20, filter: "blur(10px)" }}
                    transition={{ duration: 0.4, ease: "easeOut" }}
                    className="hero-headline-changing"
                  >
                    {words[activeWord]}
                  </motion.span>
                </AnimatePresence>
              </span>
            </h1>

            <motion.p
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="hero-subtext"
            >
              Snap a photo. Get instant nutrition data. Track meals, hydration,
              and streaks — all powered by AI.
            </motion.p>

            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="hero-cta-row"
            >
              <Magnet padding={80} magnetStrength={0.25}>
                <button
                  className="hero-cta-primary"
                  onClick={handleGetStarted}
                  id="hero-cta-start"
                >
                  Go to Dashboard <ArrowRight size={18} style={{ marginLeft: 8 }} />
                </button>
              </Magnet>
              <button
                className="hero-cta-secondary"
                onClick={handleGetStarted}
                id="hero-cta-how"
              >
                See How It Works
              </button>
            </motion.div>

            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              transition={{ delay: 1, duration: 0.8 }}
              className="hero-pills"
            >
              {[
                "Zero Friction",
                "AI Vision",
                "Streak Rewards",
                "Works Offline",
              ].map((pill, i) => (
                <span key={i} className="hero-pill">
                  <span className="hero-pill-dot" />
                  {pill}
                </span>
              ))}
            </motion.div>
          </div>

          {/* RIGHT: Visual */}
          <div className="hero-visual-col">
            {/* Runners PNG — animated with scroll parallax */}
            <motion.div
              className="runner-parallax-wrapper"
              style={{ y: runnerY, opacity: runnerOpacity }}
            >
              <div className="runner-image-container">
                <img
                  src="/elements/runners-city.png"
                  alt="Athletes running — NutriSnap fuels your performance"
                  className="runner-image"
                />
                <div className="runner-glow" />
              </div>
            </motion.div>

            {/* Floating calorie badge */}
            <motion.div
              className="hero-floating-badge"
              animate={{ y: [0, -10, 0] }}
              transition={{ repeat: Infinity, duration: 3, ease: "easeInOut" }}
            >
              <span className="hero-floating-icon">
                <Zap size={22} fill="currentColor" />
              </span>
              <div>
                <div className="hero-floating-num">2,400</div>
                <div className="hero-floating-sub">kcal tracked today</div>
              </div>
            </motion.div>

            {/* Floating protein badge */}
            <motion.div
              className="hero-floating-badge hero-floating-badge-2"
              animate={{ y: [0, 10, 0] }}
              transition={{
                repeat: Infinity,
                duration: 4,
                ease: "easeInOut",
                delay: 1,
              }}
            >
              <span className="hero-floating-icon">
                <Dumbbell size={22} fill="currentColor" />
              </span>
              <div>
                <div className="hero-floating-num">148g</div>
                <div className="hero-floating-sub">protein logged</div>
              </div>
            </motion.div>
          </div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          3D FOOD MODEL SHOWCASE
      ═══════════════════════════════════════ */}
      <section className="model-section">
        <div className="model-section-inner">
          <motion.div
            className="model-text-col"
            initial={{ opacity: 0, x: -40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            <div className="section-badge">NEXT-GEN SCANNING</div>
            <h2 className="section-title">
              SEE YOUR FOOD
              <br />
              <span className="section-title-accent">IN A NEW DIMENSION</span>
            </h2>
            <p className="model-desc">
              Our AI doesn't just recognize food — it understands volume,
              density and portion size using depth analysis, giving you macro
              estimates accurate to within 5%.
            </p>
            <div className="model-stats-row">
              {[
                ["97%", "Avg. Accuracy"],
                ["5k+", "Food Types"],
                ["<2s", "Analysis Time"],
              ].map(([val, label]) => (
                <div key={label} className="model-stat-chip">
                  <span className="model-stat-val">{val}</span>
                  <span className="model-stat-label">{label}</span>
                </div>
              ))}
            </div>
          </motion.div>

          <motion.div
            className="model-viewer-col"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            <div className="model-viewer-glow" />
            <BorderGlow
              backgroundColor="rgba(10,8,18,0.85)"
              glowColor="15 80 70"
              colors={["#FF6B5A", "#FFB347", "#3ECFA0"]}
              borderRadius={28}
              glowRadius={50}
              glowIntensity={1.1}
              animated={true}
            >
              <div className="model-viewer-card">
                <div className="model-viewer-header">
                  <span className="model-scan-badge">
                    <Search size={14} style={{ marginRight: 6 }} />
                    AI ANALYZING...
                  </span>
                  <span className="model-confidence">97% confidence</span>
                </div>
                <ModelViewer
                  url="https://raw.githubusercontent.com/KhronosGroup/glTF-Sample-Models/main/2.0/Avocado/glTF-Binary/Avocado.glb"
                  width={300}
                  height={280}
                  enableMouseParallax={true}
                  enableHoverRotation={true}
                  environmentPreset="forest"
                  autoRotate={true}
                  autoRotateSpeed={0.4}
                  alt="3D Avocado food model"
                />
                <div className="model-macro-strip">
                  {[
                    { label: "Cal", val: "234", color: "#FF6B5A" },
                    { label: "Protein", val: "3g", color: "#3ECFA0" },
                    { label: "Carbs", val: "12g", color: "#FFB347" },
                    { label: "Fat", val: "21g", color: "#6B3FA0" },
                  ].map((m) => (
                    <div key={m.label} className="model-macro-item">
                      <span
                        className="model-macro-val"
                        style={{ color: m.color }}
                      >
                        {m.val}
                      </span>
                      <span className="model-macro-label">{m.label}</span>
                    </div>
                  ))}
                </div>
              </div>
            </BorderGlow>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          FEATURES SECTION — BorderGlow cards
      ═══════════════════════════════════════ */}
      <section className="features-section">
        <motion.div
          className="section-header"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
        >
          <div className="section-badge">WHAT YOU GET</div>
          <h2 className="section-title">
            EVERYTHING YOU NEED
            <br />
            <span className="section-title-accent">NOTHING YOU DON'T</span>
          </h2>
        </motion.div>

        <div className="features-grid-new">
          {FEATURES.map((feature, i) => (
            <FeatureCard key={i} feature={feature} index={i} />
          ))}
        </div>
      </section>

      {/* ═══════════════════════════════════════
          HOW IT WORKS — Nutrition Preview
      ═══════════════════════════════════════ */}
      <section className="how-section">
        <div className="how-layout">
          <div className="how-text-col">
            <div className="section-badge">THE PROCESS</div>
            <h2 className="section-title">
              THREE STEPS.
              <br />
              <span className="section-title-accent">TOTAL CLARITY.</span>
            </h2>

            <div className="how-steps">
              <HowStep
                step="01"
                title="Snap Your Meal"
                desc="Open the app, take a photo or type a meal name. Our AI classifies it instantly using computer vision trained on the Nutrition5k dataset."
                delay={0.1}
              />
              <HowStep
                step="02"
                title="Review Your Macros"
                desc="Get instant calorie, protein, carb, and fat breakdowns. Adjust portion size with the slider for precise tracking."
                delay={0.2}
              />
              <HowStep
                step="03"
                title="Build Your Momentum"
                desc="Earn XP, build streaks, and unlock badges for consistency. Weekly AI insights keep you on track toward your goal."
                delay={0.3}
              />
            </div>
          </div>

          <motion.div
            className="how-visual-col"
            initial={{ opacity: 0, x: 40 }}
            whileInView={{ opacity: 1, x: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.7 }}
          >
            <BorderGlow
              backgroundColor="rgba(10,8,18,0.95)"
              glowColor="15 80 70"
              colors={["#FF6B5A", "#FFB347", "#3ECFA0"]}
              borderRadius={28}
              glowRadius={40}
              glowIntensity={1}
              animated={true}
            >
              <div className="nutrition-preview-card">
                <div className="nutrition-preview-header">
                  <img
                    src="https://images.unsplash.com/photo-1512621776951-a57141f2eefd?w=300&auto=format&fit=crop"
                    alt="Tracked meal"
                    className="nutrition-preview-img"
                  />
                  <div className="nutrition-preview-badge">AI ANALYZED ✓</div>
                </div>
                <div className="nutrition-preview-name">Quinoa Power Bowl</div>
                <div className="nutrition-preview-confidence">
                  97% confidence
                </div>

                <div className="nutrition-macros">
                  {[
                    {
                      label: "Calories",
                      value: 450,
                      unit: "kcal",
                      color: "#FF6B5A",
                      pct: 0.7,
                    },
                    {
                      label: "Protein",
                      value: 28,
                      unit: "g",
                      color: "#3ECFA0",
                      pct: 0.55,
                    },
                    {
                      label: "Carbs",
                      value: 52,
                      unit: "g",
                      color: "#FFB347",
                      pct: 0.65,
                    },
                    {
                      label: "Fat",
                      value: 14,
                      unit: "g",
                      color: "#6B3FA0",
                      pct: 0.4,
                    },
                  ].map((macro) => (
                    <div key={macro.label} className="macro-row">
                      <div className="macro-row-label">
                        <span>{macro.label}</span>
                        <span style={{ color: macro.color }}>
                          {macro.value}
                          {macro.unit}
                        </span>
                      </div>
                      <div className="macro-row-bar">
                        <motion.div
                          className="macro-row-fill"
                          initial={{ width: 0 }}
                          whileInView={{ width: `${macro.pct * 100}%` }}
                          viewport={{ once: true }}
                          transition={{
                            duration: 1,
                            delay: 0.5,
                            ease: "easeOut",
                          }}
                          style={{ background: macro.color }}
                        />
                      </div>
                    </div>
                  ))}
                </div>

                <button
                  className="nutrition-preview-cta"
                  onClick={handleGetStarted}
                  id="how-cta-log"
                >
                  Log This Meal{" "}
                  <ArrowRight size={18} style={{ marginLeft: 8 }} />
                </button>
              </div>
            </BorderGlow>
          </motion.div>
        </div>
      </section>

      {/* ═══════════════════════════════════════
          FINAL CTA SECTION
      ═══════════════════════════════════════ */}
      <section className="final-cta-section">
        <div className="final-cta-orb" />
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.7 }}
          className="final-cta-content"
        >
          <div className="section-badge">GET STARTED</div>
          <h2 className="final-cta-headline">
            READY TO FUEL
            <br />
            <span className="final-cta-accent">YOUR BEST SELF?</span>
          </h2>
          <p className="final-cta-sub">
            No account needed. Just snap your first meal and
            start tracking instantly.
          </p>
          <Magnet padding={100} magnetStrength={0.3}>
            <button
              className="hero-cta-primary final-cta-btn"
              onClick={handleGetStarted}
              id="final-cta-start"
            >
              <Rocket size={20} style={{ marginRight: 10 }} /> Start Now —
              It's Free
            </button>
          </Magnet>
        </motion.div>
      </section>
    </div>
  );
}

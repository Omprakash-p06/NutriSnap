import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Mic, MicOff, Loader2 } from "lucide-react";

/**
 * VoiceControl
 * Handles speech-to-text input using the Web Speech API.
 */
export default function VoiceControl({ onResult, isAnalyzing }) {
  const [isListening, setIsListening] = useState(false);
  const [supported, setSupported] = useState(true);

  useEffect(() => {
    if (
      !("webkitSpeechRecognition" in window) &&
      !("SpeechRecognition" in window)
    ) {
      setSupported(false);
    }
  }, []);

  const startListening = () => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();

    recognition.lang = "en-US";
    recognition.interimResults = false;
    recognition.maxAlternatives = 1;

    recognition.onstart = () => setIsListening(true);
    recognition.onerror = (event) => {
      console.error("Speech Recognition Error:", event.error);
      setIsListening(false);
    };
    recognition.onend = () => setIsListening(false);

    recognition.onresult = (event) => {
      const transcript = event.results[0][0].transcript;
      onResult(transcript);
    };

    recognition.start();
  };

  if (!supported) return null;

  return (
    <div className="voice-control-wrapper" style={{ position: "relative" }}>
      <motion.button
        type="button"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        disabled={isAnalyzing}
        onClick={startListening}
        className={`clay-btn voice-btn ${isListening ? "listening" : ""}`}
        style={{
          width: "50px",
          height: "50px",
          borderRadius: "50%",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: isListening ? "#FF6B5A" : "var(--accent-mint)",
          border: "none",
          boxShadow: isListening ? "0 0 20px rgba(255, 107, 90, 0.4)" : "none",
          cursor: "pointer",
        }}
      >
        <AnimatePresence mode="wait">
          {isListening ? (
            <motion.div
              key="mic-off"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
            >
              <MicOff size={24} color="#fff" />
            </motion.div>
          ) : (
            <motion.div
              key="mic-on"
              initial={{ scale: 0 }}
              animate={{ scale: 1 }}
              exit={{ scale: 0 }}
            >
              <Mic size={24} color="#fff" />
            </motion.div>
          )}
        </AnimatePresence>
      </motion.button>

      {isListening && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="voice-tip"
          style={{
            position: "absolute",
            top: "60px",
            left: "50%",
            transform: "translateX(-50%)",
            background: "rgba(0,0,0,0.8)",
            color: "#fff",
            padding: "4px 12px",
            borderRadius: "12px",
            fontSize: "0.75rem",
            whiteSpace: "nowrap",
            zIndex: 100,
          }}
        >
          Listening...
        </motion.div>
      )}
    </div>
  );
}

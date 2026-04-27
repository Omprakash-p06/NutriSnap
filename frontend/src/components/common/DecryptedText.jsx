import { useState, useEffect, useRef } from 'react';
import { motion } from 'framer-motion';

/**
 * DecryptedText
 * An AI-themed text reveal that cycles through characters.
 */
export default function DecryptedText({ 
  text, 
  speed = 50, 
  revealDuration = 1000, 
  characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*()_+",
  className = ""
}) {
  const [displayText, setDisplayText] = useState("");
  const [isRevealed, setIsRevealed] = useState(false);
  const intervalRef = useRef(null);

  useEffect(() => {
    let iteration = 0;
    const totalIterations = text.length + 10; // Extra room for jumble

    setDisplayText(
      text.split("").map(() => characters[Math.floor(Math.random() * characters.length)]).join("")
    );

    intervalRef.current = setInterval(() => {
      setDisplayText((prev) => 
        text.split("").map((char, index) => {
          if (index < iteration) {
            return text[index];
          }
          return characters[Math.floor(Math.random() * characters.length)];
        }).join("")
      );

      if (iteration >= text.length) {
        clearInterval(intervalRef.current);
        setIsRevealed(true);
      }
      
      iteration += 1/3; // Slow down the reveal
    }, speed);

    return () => clearInterval(intervalRef.current);
  }, [text, speed, characters]);

  return (
    <span className={`decrypted-text ${className} ${isRevealed ? 'revealed' : 'decrypting'}`}>
      {displayText}
    </span>
  );
}

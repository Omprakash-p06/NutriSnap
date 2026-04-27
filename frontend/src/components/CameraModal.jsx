import { useEffect, useRef, useState } from 'react';
import { Camera, RefreshCcw, X } from 'lucide-react';

export default function CameraModal({ isOpen, onClose, onCapture }) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [stream, setStream] = useState(null);
  const [facingMode, setFacingMode] = useState('environment'); // default to rear camera

  useEffect(() => {
    if (!isOpen) {
      stopCamera();
      return;
    }

    startCamera(facingMode);
    
    // Cleanup on unmount or close
    return () => stopCamera();
  }, [isOpen, facingMode]);

  const startCamera = async (mode) => {
    stopCamera(); // Stop any existing streams before requesting new ones
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ 
        video: { facingMode: mode } 
      });
      setStream(mediaStream);
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
      }
    } catch (err) {
      alert("Camera access denied or unavailable.");
      onClose();
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
  };

  const handleCapture = () => {
    if (videoRef.current && canvasRef.current) {
      const video = videoRef.current;
      const canvas = canvasRef.current;
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext('2d');
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
      const dataUrl = canvas.toDataURL('image/jpeg');
      onCapture(dataUrl);
      onClose();
    }
  };

  const toggleCamera = () => {
    setFacingMode(prev => prev === 'environment' ? 'user' : 'environment');
  };

  if (!isOpen) return null;

  return (
    <div style={styles.fullscreenOverlay}>
      {/* Absolute Close Button */}
      <button style={styles.closeBtn} onClick={onClose}>
        <X size={28} />
      </button>

      {/* Main Viewfinder */}
      <video
        ref={videoRef}
        autoPlay
        playsInline
        muted
        style={styles.viewfinder}
      />
      <canvas ref={canvasRef} style={{ display: 'none' }} />

      {/* Camera Controls Bar */}
      <div className="glass-panel" style={styles.controlsBar}>
        
        {/* Helper text / Empty div for flex balance */}
        <div style={{ flex: 1 }}></div>

        {/* Shutter Button */}
        <button style={styles.shutterBtn} onClick={handleCapture}>
          <div style={styles.shutterInner}></div>
        </button>

        {/* Flip Camera */}
        <div style={{ flex: 1, display: 'flex', justifyContent: 'flex-end' }}>
          <button style={styles.flipBtn} onClick={toggleCamera}>
            <RefreshCcw size={24} color="#FFF" />
          </button>
        </div>

      </div>
    </div>
  );
}

const styles = {
  fullscreenOverlay: {
    position: 'fixed',
    top: 0, left: 0, right: 0, bottom: 0,
    backgroundColor: '#000',
    zIndex: 2000,
    display: 'flex',
    flexDirection: 'column'
  },
  viewfinder: {
    flex: 1,
    width: '100%',
    height: '100%',
    objectFit: 'cover'
  },
  closeBtn: {
    position: 'absolute',
    top: '20px',
    left: '20px',
    background: 'rgba(0, 0, 0, 0.5)',
    border: 'none',
    color: '#FFF',
    fontSize: '2rem',
    cursor: 'pointer',
    zIndex: 2001,
    width: '44px',
    height: '44px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center'
  },
  controlsBar: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    height: '120px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    padding: '0 40px',
    background: 'linear-gradient(to top, rgba(0,0,0,0.8), rgba(0,0,0,0))',
    borderBottom: 'none' // Override generic glass panel border
  },
  shutterBtn: {
    width: '72px',
    height: '72px',
    borderRadius: '50%',
    backgroundColor: 'transparent',
    border: '4px solid #FFF',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    padding: 0
  },
  shutterInner: {
    width: '56px',
    height: '56px',
    backgroundColor: '#FFF',
    borderRadius: '50%',
    transition: 'transform 0.1s'
  },
  flipBtn: {
    background: 'rgba(255, 255, 255, 0.2)',
    border: 'none',
    width: '48px',
    height: '48px',
    borderRadius: '50%',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    cursor: 'pointer',
    backdropFilter: 'blur(10px)'
  }
};

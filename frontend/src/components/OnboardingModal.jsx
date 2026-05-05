import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './OnboardingModal.css';

export default function OnboardingModal({ isOpen, onClose }) {
  const { userProfile, updateProfile } = useAuth();
  const [gender, setGender] = useState(userProfile?.gender || 'male');
  const [weight, setWeight] = useState(userProfile?.weight || '');
  const [height, setHeight] = useState(userProfile?.height || '');

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    updateProfile({
      gender,
      weight: parseFloat(weight),
      height: parseFloat(height),
    });
    onClose();
  };

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-modal clay-card">
        <h2 className="onboarding-title">Welcome to NutriSnap!</h2>
        <p className="onboarding-subtitle">Tell us a bit about yourself to get started with BMI calculation and personalized goals.</p>
        
        <form onSubmit={handleSubmit} className="onboarding-form">
          <div className="form-group">
            <label>Gender</label>
            <div className="gender-options">
              {['male', 'female', 'other'].map((option) => (
                <button
                  key={option}
                  type="button"
                  className={`gender-btn ${gender === option ? 'active' : ''}`}
                  onClick={() => setGender(option)}
                >
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </button>
              ))}
            </div>
          </div>
          
          <div className="form-group">
            <label htmlFor="weight">Weight (kg)</label>
            <input
              id="weight"
              type="number"
              value={weight}
              onChange={(e) => setWeight(e.target.value)}
              placeholder="e.g. 70"
              required
              className="clay-input"
            />
          </div>
          
          <div className="form-group">
            <label htmlFor="height">Height (cm)</label>
            <input
              id="height"
              type="number"
              value={height}
              onChange={(e) => setHeight(e.target.value)}
              placeholder="e.g. 175"
              required
              className="clay-input"
            />
          </div>
          
          <button type="submit" className="clay-btn onboarding-submit">
            Save & Continue
          </button>
        </form>
      </div>
    </div>
  );
}

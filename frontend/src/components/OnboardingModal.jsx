import React, { useState } from 'react';
import { useAuth } from '../context/AuthContext';
import './OnboardingModal.css';

export default function OnboardingModal({ isOpen, onClose }) {
  const { userProfile, updateProfile } = useAuth();
  const [age, setAge] = useState(userProfile?.age || '');
  const [sex, setSex] = useState(userProfile?.sex || 'male');
  const [weight, setWeight] = useState(userProfile?.weight || '');
  const [height, setHeight] = useState(userProfile?.height || '');
  const [activityLevel, setActivityLevel] = useState(userProfile?.activityLevel || '1.2');
  const [goal, setGoal] = useState(userProfile?.goal || 'maintain');
  const [dietaryPreferences, setDietaryPreferences] = useState(userProfile?.dietaryPreferences || []);

  if (!isOpen) return null;

  const handleSubmit = (e) => {
    e.preventDefault();
    updateProfile({
      age: parseInt(age),
      sex,
      weight: parseFloat(weight),
      height: parseFloat(height),
      activityLevel: parseFloat(activityLevel),
      goal,
      dietaryPreferences,
    });
    onClose();
  };

  const toggleDietaryPreference = (pref) => {
    setDietaryPreferences(prev => 
      prev.includes(pref) ? prev.filter(p => p !== pref) : [...prev, pref]
    );
  };

  return (
    <div className="onboarding-overlay">
      <div className="onboarding-modal clay-card">
        <h2 className="onboarding-title">Welcome to NutriSnap!</h2>
        <p className="onboarding-subtitle">Tell us a bit about yourself for personalized nutrition tracking.</p>
        
        <form onSubmit={handleSubmit} className="onboarding-form">
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="age">Age</label>
              <input
                id="age"
                type="number"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                placeholder="25"
                required
                className="clay-input"
              />
            </div>
            <div className="form-group">
              <label>Sex (assigned at birth)</label>
              <div className="gender-options">
                {['male', 'female'].map((option) => (
                  <button
                    key={option}
                    type="button"
                    className={`gender-btn ${sex === option ? 'active' : ''}`}
                    onClick={() => setSex(option)}
                  >
                    {option.charAt(0).toUpperCase() + option.slice(1)}
                  </button>
                ))}
              </div>
            </div>
          </div>
          
          <div className="form-row">
            <div className="form-group">
              <label htmlFor="weight">Weight (kg)</label>
              <input
                id="weight"
                type="number"
                value={weight}
                onChange={(e) => setWeight(e.target.value)}
                placeholder="70"
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
                placeholder="175"
                required
                className="clay-input"
              />
            </div>
          </div>

          <div className="form-group">
            <label htmlFor="activityLevel">Activity Level</label>
            <select 
              id="activityLevel" 
              value={activityLevel} 
              onChange={(e) => setActivityLevel(e.target.value)}
              className="clay-input"
            >
              <option value="1.2">Sedentary (Little to no exercise)</option>
              <option value="1.375">Lightly Active (1-3 days/week)</option>
              <option value="1.55">Moderately Active (3-5 days/week)</option>
              <option value="1.725">Very Active (6-7 days/week)</option>
              <option value="1.9">Extra Active (Hard exercise/Physical job)</option>
            </select>
          </div>

          <div className="form-group">
            <label>Primary Goal</label>
            <div className="goal-options">
              {[
                { id: 'lose', label: 'Lose Weight' },
                { id: 'maintain', label: 'Maintain' },
                { id: 'gain', label: 'Gain Muscle' }
              ].map((option) => (
                <button
                  key={option.id}
                  type="button"
                  className={`goal-btn ${goal === option.id ? 'active' : ''}`}
                  onClick={() => setGoal(option.id)}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>

          <div className="form-group">
            <label>Dietary Preferences</label>
            <div className="dietary-options">
              {['Vegetarian', 'Vegan', 'Keto', 'Paleo', 'Gluten-Free', 'Dairy-Free'].map((pref) => (
                <button
                  key={pref}
                  type="button"
                  className={`pref-btn ${dietaryPreferences.includes(pref) ? 'active' : ''}`}
                  onClick={() => toggleDietaryPreference(pref)}
                >
                  {pref}
                </button>
              ))}
            </div>
          </div>
          
          <button type="submit" className="clay-btn onboarding-submit">
            Save & Continue
          </button>
        </form>
      </div>
    </div>
  );
}

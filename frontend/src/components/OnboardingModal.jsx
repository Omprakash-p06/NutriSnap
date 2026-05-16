import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import { User, Activity, Target, Utensils, ChevronRight, X } from 'lucide-react';
import ShinyText from './common/ShinyText';

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
    <AnimatePresence>
      <div className="fixed inset-0 z-[10000] flex items-center justify-center p-4">
        <motion.div 
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-black/90 backdrop-blur-md"
          onClick={onClose}
        />
        
        <motion.div 
          initial={{ scale: 0.9, opacity: 0, y: 20 }}
          animate={{ scale: 1, opacity: 1, y: 0 }}
          exit={{ scale: 0.9, opacity: 0, y: 20 }}
          className="relative w-full max-w-xl bg-zinc-950 border border-zinc-800 rounded-[32px] shadow-2xl overflow-hidden"
        >
          {/* Header */}
          <div className="p-8 pb-0 text-center relative">
            <button 
              onClick={onClose}
              className="absolute top-6 right-6 p-2 text-zinc-500 hover:text-white transition-colors"
            >
              <X size={20} />
            </button>
            <div className="w-16 h-16 bg-zinc-900 rounded-2xl flex items-center justify-center mx-auto mb-6 border border-zinc-800">
              <User className="text-emerald-500" size={32} />
            </div>
            <h2 className="text-3xl font-black text-white tracking-tight mb-2">Personalize NutriSnap</h2>
            <p className="text-zinc-400 text-sm">We use these metrics to calculate your custom calorie and macro targets.</p>
          </div>

          <form onSubmit={handleSubmit} className="p-8 pt-6 space-y-6 max-h-[70vh] overflow-y-auto custom-scrollbar">
            {/* Physical Metrics */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Age</label>
                <input
                  type="number"
                  value={age}
                  onChange={(e) => setAge(e.target.value)}
                  placeholder="25"
                  required
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-white focus:border-emerald-500 outline-none transition-all"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Sex</label>
                <div className="flex bg-zinc-900 p-1 rounded-2xl border border-zinc-800 h-[58px]">
                  {['male', 'female'].map((option) => (
                    <button
                      key={option}
                      type="button"
                      className={`flex-1 rounded-xl text-xs font-bold transition-all ${
                        sex === option ? 'bg-zinc-800 text-white shadow-lg' : 'text-zinc-500 hover:text-zinc-300'
                      }`}
                      onClick={() => setSex(option)}
                    >
                      {option.charAt(0).toUpperCase() + option.slice(1)}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Weight (kg)</label>
                <input
                  type="number"
                  step="0.1"
                  value={weight}
                  onChange={(e) => setWeight(e.target.value)}
                  placeholder="70.5"
                  required
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-white focus:border-emerald-500 outline-none transition-all"
                />
              </div>
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Height (cm)</label>
                <input
                  type="number"
                  value={height}
                  onChange={(e) => setHeight(e.target.value)}
                  placeholder="175"
                  required
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-white focus:border-emerald-500 outline-none transition-all"
                />
              </div>
            </div>

            {/* Activity & Goal */}
            <div className="space-y-4">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Activity Level</label>
                <select 
                  value={activityLevel} 
                  onChange={(e) => setActivityLevel(e.target.value)}
                  className="w-full bg-zinc-900 border border-zinc-800 rounded-2xl p-4 text-white focus:border-emerald-500 outline-none transition-all appearance-none"
                >
                  <option value="1.2">Sedentary (Little to no exercise)</option>
                  <option value="1.375">Lightly Active (1-3 days/week)</option>
                  <option value="1.55">Moderately Active (3-5 days/week)</option>
                  <option value="1.725">Very Active (6-7 days/week)</option>
                  <option value="1.9">Extra Active (Hard exercise/Physical job)</option>
                </select>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Primary Goal</label>
                <div className="grid grid-cols-3 gap-2">
                  {[
                    { id: 'lose', label: 'Lose Weight' },
                    { id: 'maintain', label: 'Maintain' },
                    { id: 'gain', label: 'Gain Muscle' }
                  ].map((option) => (
                    <button
                      key={option.id}
                      type="button"
                      className={`p-3 rounded-2xl border text-[11px] font-bold transition-all ${
                        goal === option.id 
                          ? 'bg-emerald-500/10 border-emerald-500/50 text-emerald-400' 
                          : 'bg-zinc-900 border-zinc-800 text-zinc-500 hover:border-zinc-700'
                      }`}
                      onClick={() => setGoal(option.id)}
                    >
                      {option.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Dietary Preferences */}
            <div className="space-y-2">
              <label className="text-[10px] font-black uppercase tracking-widest text-zinc-500 ml-1">Dietary Preferences</label>
              <div className="flex flex-wrap gap-2">
                {['Vegetarian', 'Vegan', 'Keto', 'Paleo', 'Gluten-Free', 'Dairy-Free'].map((pref) => (
                  <button
                    key={pref}
                    type="button"
                    className={`px-4 py-2 rounded-full border text-[10px] font-black transition-all ${
                      dietaryPreferences.includes(pref) 
                        ? 'bg-white text-black border-white' 
                        : 'bg-zinc-950 border-zinc-800 text-zinc-400 hover:border-zinc-600'
                    }`}
                    onClick={() => toggleDietaryPreference(pref)}
                  >
                    {pref}
                  </button>
                ))}
              </div>
            </div>

            {/* Submit */}
            <button 
              type="submit" 
              className="w-full py-5 bg-white text-black rounded-[24px] font-black text-lg hover:bg-zinc-200 transition-all flex items-center justify-center gap-2 mt-4"
            >
              <ShinyText text="Start Journey" baseColor="#000" />
              <ChevronRight size={20} />
            </button>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}

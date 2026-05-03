import React, { useState } from "react";
import { Settings, X, Save, Target } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const SettingsModal = ({ isOpen, onClose }) => {
  const { userSettings, updateUserSettings } = useAuth();
  const [formData, setFormData] = useState({
    dailyCalorieGoal: userSettings.dailyCalorieGoal || 2000,
    proteinGoal: userSettings.proteinGoal || 150,
    carbsGoal: userSettings.carbsGoal || 200,
    fatGoal: userSettings.fatGoal || 70,
  });

  const [saving, setSaving] = useState(false);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    await updateUserSettings(formData);
    setSaving(false);
    onClose();
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: parseInt(value) || 0 }));
  };

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div
        className="modal-content glass-card"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header">
          <div className="flex items-center gap-2">
            <Settings className="text-secondary" size={24} />
            <h2 className="fredoka">Daily Goals</h2>
          </div>
          <button className="close-btn" onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="settings-form">
          <div className="setting-group">
            <label className="flex items-center gap-2 mb-2">
              <Target size={16} className="text-primary" />
              <span>Daily Calorie Target</span>
            </label>
            <input
              type="number"
              name="dailyCalorieGoal"
              value={formData.dailyCalorieGoal}
              onChange={handleChange}
              className="settings-input"
            />
          </div>

          <div
            className="macros-grid mt-4"
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(3, 1fr)",
              gap: "15px",
            }}
          >
            <div className="setting-group">
              <label>Protein (g)</label>
              <input
                type="number"
                name="proteinGoal"
                value={formData.proteinGoal}
                onChange={handleChange}
                className="settings-input"
              />
            </div>
            <div className="setting-group">
              <label>Carbs (g)</label>
              <input
                type="number"
                name="carbsGoal"
                value={formData.carbsGoal}
                onChange={handleChange}
                className="settings-input"
              />
            </div>
            <div className="setting-group">
              <label>Fat (g)</label>
              <input
                type="number"
                name="fatGoal"
                value={formData.fatGoal}
                onChange={handleChange}
                className="settings-input"
              />
            </div>
          </div>

          <button
            type="submit"
            className={`clay-btn w-full mt-6 flex items-center justify-center gap-2 ${saving ? "opacity-50" : ""}`}
            disabled={saving}
          >
            <Save size={18} />
            {saving ? "Saving..." : "Save Settings"}
          </button>
        </form>
      </div>

      <style jsx>{`
        .settings-form {
          padding: 20px 0;
        }
        .setting-group label {
          font-size: 0.9rem;
          color: var(--text-secondary);
        }
        .settings-input {
          width: 100%;
          padding: 12px;
          border-radius: 12px;
          border: 1px solid rgba(0, 0, 0, 0.1);
          background: rgba(255, 255, 255, 0.5);
          font-family: inherit;
          font-size: 1.1rem;
          outline: none;
          transition: border-color 0.2s;
        }
        .settings-input:focus {
          border-color: var(--primary);
        }
        .w-full {
          width: 100%;
        }
        .mt-6 {
          margin-top: 24px;
        }
      `}</style>
    </div>
  );
};

export default SettingsModal;

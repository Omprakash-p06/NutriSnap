import React, { useState, useEffect } from "react";
import { Settings, X, Save, Target, User, MapPin, Scale, Ruler, Calendar, Activity, Sparkles } from "lucide-react";
import { useAuth } from "../context/AuthContext";

const SettingsModal = ({ isOpen, onClose }) => {
  const { currentUser, userProfile, updateProfile, userSettings, updateUserSettings, token } = useAuth();
  
  const [formData, setFormData] = useState({
    name: "",
    age: "",
    weight: "",
    height: "",
    location: "",
    gender: "male",
    activityLevel: "1.55",
    goal: "maintain",
    dailyCalorieGoal: 2000,
    proteinGoal: 150,
    carbsGoal: 200,
    fatGoal: 70,
  });

  const [saving, setSaving] = useState(false);
  const [generatingGoals, setGeneratingGoals] = useState(false);
  const [aiReasoning, setAiReasoning] = useState("");

  useEffect(() => {
    if (isOpen && currentUser) {
      setFormData({
        name: currentUser.full_name || "",
        age: currentUser.age || "",
        weight: currentUser.weight_kg || "",
        height: currentUser.height_cm || "",
        location: currentUser.location || "",
        gender: currentUser.gender || "male",
        activityLevel: currentUser.activity_level || "1.55",
        goal: currentUser.goal || "maintain",
        dailyCalorieGoal: userSettings.dailyCalorieGoal || 2000,
        proteinGoal: userSettings.proteinGoal || 150,
        carbsGoal: userSettings.carbsGoal || 200,
        fatGoal: userSettings.fatGoal || 70,
      });
      setAiReasoning("");
    }
  }, [isOpen, currentUser, userSettings]);

  if (!isOpen) return null;

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    
    const customSettings = {
      ...(currentUser?.settings || {}),
      dailyCalorieGoal: parseInt(formData.dailyCalorieGoal),
      proteinGoal: parseInt(formData.proteinGoal),
      carbsGoal: parseInt(formData.carbsGoal),
      fatGoal: parseInt(formData.fatGoal),
    };

    // Update Profile (Syncs to backend with persistent custom settings)
    await updateProfile({
      name: formData.name,
      age: formData.age,
      weight: formData.weight,
      height: formData.height,
      location: formData.location,
      sex: formData.gender,
      activityLevel: formData.activityLevel,
      goal: formData.goal,
      settings: customSettings,
    });

    // Update Local Goals
    updateUserSettings(customSettings);

    setSaving(false);
    onClose();
  };

  const handleGenerateGoals = async () => {
    setGeneratingGoals(true);
    setAiReasoning("");
    try {
      const res = await fetch("/api/users/generate-targets", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: JSON.stringify({
          weight_kg: formData.weight ? parseFloat(formData.weight) : null,
          height_cm: formData.height ? parseFloat(formData.height) : null,
          age: formData.age ? parseInt(formData.age) : null,
          gender: formData.gender,
          activity_level: formData.activityLevel,
          goal: formData.goal,
        }),
      });

      if (res.ok) {
        const data = await res.json();
        setFormData((prev) => ({
          ...prev,
          dailyCalorieGoal: data.dailyCalorieGoal,
          proteinGoal: data.proteinGoal,
          carbsGoal: data.carbsGoal,
          fatGoal: data.fatGoal,
        }));
        setAiReasoning(data.reasoning);
      } else {
        console.error("Failed to generate goals via AI");
      }
    } catch (err) {
      console.error("Error generating goals via AI:", err);
    } finally {
      setGeneratingGoals(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  return (
    <div className="modal-overlay" style={styles.overlay} onClick={onClose}>
      <div
        className="modal-content glass-card"
        style={styles.modal}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="modal-header" style={styles.header}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <Settings className="text-secondary" size={24} />
            <h2 className="fredoka" style={{ margin: 0 }}>Settings</h2>
          </div>
          <button style={styles.closeBtn} onClick={onClose}>
            <X size={20} />
          </button>
        </div>

        <form onSubmit={handleSubmit} style={styles.form}>
          <div style={styles.scrollArea}>
            <h3 style={styles.sectionTitle}>Account Profile</h3>
            
            <div style={styles.inputGroup}>
              <label style={styles.label}><User size={14} /> Full Name</label>
              <input
                type="text"
                name="name"
                value={formData.name}
                onChange={handleChange}
                placeholder="John Doe"
                style={styles.input}
              />
            </div>

            <div style={styles.grid2}>
              <div style={styles.inputGroup}>
                <label style={styles.label}><Calendar size={14} /> Age</label>
                <input
                  type="number"
                  name="age"
                  value={formData.age}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}><MapPin size={14} /> Location</label>
                <input
                  type="text"
                  name="location"
                  value={formData.location}
                  onChange={handleChange}
                  placeholder="New York, USA"
                  style={styles.input}
                />
              </div>
            </div>

            <div style={styles.grid2}>
              <div style={styles.inputGroup}>
                <label style={styles.label}><Scale size={14} /> Weight (kg)</label>
                <input
                  type="number"
                  name="weight"
                  step="0.1"
                  value={formData.weight}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}><Ruler size={14} /> Height (cm)</label>
                <input
                  type="number"
                  name="height"
                  value={formData.height}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
            </div>

             <div style={styles.grid3}>
                <div style={styles.inputGroup}>
                   <label style={styles.label}><User size={14} /> Gender</label>
                   <select name="gender" value={formData.gender} onChange={handleChange} style={styles.input}>
                     <option value="male">Male</option>
                     <option value="female">Female</option>
                   </select>
                </div>
                <div style={styles.inputGroup}>
                   <label style={styles.label}><Activity size={14} /> Activity</label>
                   <select name="activityLevel" value={formData.activityLevel} onChange={handleChange} style={styles.input}>
                     <option value="1.2">Sedentary</option>
                     <option value="1.375">Light</option>
                     <option value="1.55">Moderate</option>
                     <option value="1.725">Active</option>
                     <option value="1.9">Extra Active</option>
                   </select>
                </div>
                <div style={styles.inputGroup}>
                   <label style={styles.label}><Target size={14} /> Goal</label>
                   <select name="goal" value={formData.goal} onChange={handleChange} style={styles.input}>
                     <option value="maintain">Maintain</option>
                     <option value="lose">Weight Loss</option>
                     <option value="gain">Muscle Gain</option>
                   </select>
                </div>
             </div>

             <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginTop: "24px", marginBottom: "16px" }}>
               <h3 style={{...styles.sectionTitle, margin: 0}}>Daily Nutrition Goals</h3>
               <button
                 type="button"
                 onClick={handleGenerateGoals}
                 disabled={generatingGoals}
                 style={styles.aiBtn}
               >
                 <Sparkles size={14} style={{ animation: generatingGoals ? "pulse 1.5s infinite" : "none" }} />
                 {generatingGoals ? "Calibrating..." : "Generate with AI"}
               </button>
             </div>

             {aiReasoning && (
               <div style={styles.reasoningBox}>
                 <span style={{ fontSize: "1.25rem" }}>✨</span>
                 <div style={{ display: "flex", flexDirection: "column", gap: "2px" }}>
                    <strong style={{ fontSize: "0.85rem", color: "#ec4899" }}>AI Insight</strong>
                    <p style={{ margin: 0, fontSize: "0.82rem", color: "var(--text-muted)", lineHeight: "1.4" }}>
                      {aiReasoning}
                    </p>
                 </div>
               </div>
             )}

             <div style={styles.inputGroup}>
               <label style={styles.label}><Target size={14} /> Daily Calorie Target</label>
               <input
                 type="number"
                 name="dailyCalorieGoal"
                 value={formData.dailyCalorieGoal}
                 onChange={handleChange}
                 style={styles.input}
               />
             </div>

            <div style={styles.grid3}>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Protein (g)</label>
                <input
                  type="number"
                  name="proteinGoal"
                  value={formData.proteinGoal}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Carbs (g)</label>
                <input
                  type="number"
                  name="carbsGoal"
                  value={formData.carbsGoal}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
              <div style={styles.inputGroup}>
                <label style={styles.label}>Fat (g)</label>
                <input
                  type="number"
                  name="fatGoal"
                  value={formData.fatGoal}
                  onChange={handleChange}
                  style={styles.input}
                />
              </div>
            </div>
          </div>

          <button
            type="submit"
            className={`clay-btn ${saving ? "opacity-50" : ""}`}
            style={styles.saveBtn}
            disabled={saving}
          >
            <Save size={18} />
            {saving ? "Saving..." : "Save All Settings"}
          </button>
        </form>
      </div>
    </div>
  );
};

const styles = {
  overlay: {
    position: "fixed",
    inset: 0,
    backgroundColor: "rgba(0,0,0,0.5)",
    backdropFilter: "blur(10px)",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    zIndex: 10001,
    padding: "20px",
  },
  modal: {
    width: "100%",
    maxWidth: "500px",
    maxHeight: "90vh",
    backgroundColor: "var(--modal-bg)",
    borderRadius: "24px",
    border: "1px solid var(--border-color)",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  header: {
    padding: "24px",
    borderBottom: "1px solid var(--border-color)",
    display: "flex",
    justifyContent: "space-between",
    alignItems: "center",
  },
  closeBtn: {
    background: "none",
    border: "none",
    color: "var(--text-muted)",
    cursor: "pointer",
    padding: "4px",
  },
  form: {
    padding: "24px",
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  scrollArea: {
    overflowY: "auto",
    paddingRight: "8px",
    marginBottom: "24px",
  },
  sectionTitle: {
    fontSize: "0.8rem",
    textTransform: "uppercase",
    letterSpacing: "1px",
    color: "var(--primary)",
    marginBottom: "16px",
    fontWeight: 800,
  },
  inputGroup: {
    marginBottom: "16px",
    display: "flex",
    flexDirection: "column",
    gap: "6px",
  },
  label: {
    fontSize: "0.85rem",
    color: "var(--text-muted)",
    display: "flex",
    alignItems: "center",
    gap: "6px",
  },
  input: {
    width: "100%",
    backgroundColor: "var(--bg)",
    border: "1px solid var(--border-color)",
    borderRadius: "12px",
    padding: "12px 16px",
    color: "var(--text)",
    fontSize: "1rem",
    outline: "none",
  },
  grid2: {
    display: "grid",
    gridTemplateColumns: "1fr 1fr",
    gap: "16px",
  },
  grid3: {
    display: "grid",
    gridTemplateColumns: "repeat(3, 1fr)",
    gap: "12px",
  },
  saveBtn: {
    width: "100%",
    display: "flex",
    alignItems: "center",
    justifyContent: "center",
    gap: "10px",
    padding: "16px",
    borderRadius: "16px",
    fontSize: "1.1rem",
    fontWeight: 700,
    flexShrink: 0,
  },
  aiBtn: {
    background: "linear-gradient(135deg, #ec4899 0%, #8b5cf6 100%)",
    color: "white",
    border: "none",
    borderRadius: "10px",
    padding: "8px 12px",
    fontSize: "0.8rem",
    fontWeight: 600,
    cursor: "pointer",
    display: "flex",
    alignItems: "center",
    gap: "6px",
    boxShadow: "0 4px 12px rgba(236, 72, 153, 0.3)",
    transition: "transform 0.2s ease, box-shadow 0.2s ease",
  },
  reasoningBox: {
    backgroundColor: "rgba(236, 72, 153, 0.05)",
    border: "1px solid rgba(236, 72, 153, 0.2)",
    borderRadius: "12px",
    padding: "12px 16px",
    marginBottom: "16px",
    display: "flex",
    gap: "12px",
    alignItems: "flex-start",
    backdropFilter: "blur(5px)",
  }
};

export default SettingsModal;


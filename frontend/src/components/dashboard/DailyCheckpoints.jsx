import { useEffect, useMemo, useState } from "react";
import { CheckCircle2, Circle, Trophy } from "lucide-react";
import { useAuth } from "../../context/AuthContext";
import SpotlightCard from "../common/SpotlightCard";

const CHECKPOINT_XP_REWARD = 120;

function getDateKey(date = new Date()) {
  return date.toISOString().slice(0, 10);
}

function getStreakFromCheckpointHistory(userKey) {
  const now = new Date();
  let streak = 0;

  for (let i = 0; i < 365; i += 1) {
    const d = new Date(now);
    d.setDate(now.getDate() - i);
    const dateKey = getDateKey(d);
    const done = localStorage.getItem(`nutrisnap-checkpoints-done:${userKey}:${dateKey}`);

    if (done === "1") {
      streak += 1;
      continue;
    }

    if (i === 0) {
      continue;
    }

    break;
  }

  return streak;
}

export default function DailyCheckpoints({
  todayCalories,
  todayMeals,
  todayMacros,
}) {
  const {
    userSettings,
    userProfile,
    bmi,
    currentUser,
    addXp,
    updateUserSettings,
  } = useAuth();
  const [isClaimedToday, setIsClaimedToday] = useState(false);

  const userKey = currentUser?.email || "guest";
  const todayKey = getDateKey();

  useEffect(() => {
    const done = localStorage.getItem(
      `nutrisnap-checkpoints-done:${userKey}:${todayKey}`,
    );
    setIsClaimedToday(done === "1");
  }, [userKey, todayKey]);

  const checkpoints = useMemo(() => {
    const calorieGoal = Math.max(1200, Number(userSettings?.dailyCalorieGoal || 2000));
    const proteinGoal = Math.max(40, Number(userSettings?.proteinGoal || 150));
    const bmiVal = Number(bmi || 0);

    let calorieLabel = "Stay in your healthy calorie range";
    let calorieDone =
      todayCalories >= calorieGoal * 0.85 && todayCalories <= calorieGoal * 1.1;

    if (bmiVal >= 25) {
      calorieLabel = "Keep calories controlled for fat-loss progress";
      calorieDone = todayCalories >= calorieGoal * 0.75 && todayCalories <= calorieGoal * 1.05;
    } else if (bmiVal > 0 && bmiVal < 18.5) {
      calorieLabel = "Hit your calorie floor for healthy weight gain";
      calorieDone = todayCalories >= calorieGoal * 0.95;
    }

    return [
      {
        id: "calories",
        label: calorieLabel,
        detail: `${Math.round(todayCalories)} / ${Math.round(calorieGoal)} kcal`,
        done: calorieDone,
      },
      {
        id: "protein",
        label: "Hit your protein checkpoint",
        detail: `${Math.round(todayMacros?.protein || 0)} / ${Math.round(proteinGoal)} g`,
        done: Number(todayMacros?.protein || 0) >= proteinGoal * 0.8,
      },
      {
        id: "consistency",
        label: "Log at least 2 meals today",
        detail: `${todayMeals?.length || 0} logged`,
        done: (todayMeals?.length || 0) >= 2,
      },
    ];
  }, [todayCalories, todayMeals, todayMacros, userSettings, bmi]);

  const allDone = checkpoints.every((item) => item.done);

  useEffect(() => {
    if (!allDone || isClaimedToday) {
      return;
    }

    localStorage.setItem(`nutrisnap-checkpoints-done:${userKey}:${todayKey}`, "1");
    setIsClaimedToday(true);
    addXp(CHECKPOINT_XP_REWARD);

    const streak = getStreakFromCheckpointHistory(userKey);
    updateUserSettings({ streak }).catch(() => {
      // Keep the UI responsive even if backend update fails.
    });
  }, [allDone, isClaimedToday, userKey, todayKey, addXp, updateUserSettings]);

  const bmiText = userProfile && bmi ? `BMI ${bmi}` : "BMI not set";

  return (
    <SpotlightCard className="glass-card" style={{ padding: "18px 20px", margin: "12px 0 18px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "10px" }}>
        <div>
          <h3 style={{ margin: 0, fontSize: "1rem" }}>Daily Checkpoints</h3>
          <p style={{ margin: "4px 0 0", opacity: 0.7, fontSize: "0.82rem" }}>
            Personalized using {bmiText} and your profile goals.
          </p>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: 6, color: "var(--primary-amber)" }}>
          <Trophy size={16} />
          <span style={{ fontWeight: 700, fontSize: "0.85rem" }}>
            +{CHECKPOINT_XP_REWARD} XP
          </span>
        </div>
      </div>

      <div style={{ display: "grid", gap: "8px" }}>
        {checkpoints.map((item) => (
          <div
            key={item.id}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "10px 12px",
              borderRadius: "12px",
              border: "1px solid var(--border)",
              background: item.done
                ? "rgba(62, 207, 160, 0.12)"
                : "rgba(255,255,255,0.03)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              {item.done ? <CheckCircle2 size={16} color="#3ECFA0" /> : <Circle size={16} />}
              <div>
                <div style={{ fontSize: "0.88rem", fontWeight: 600 }}>{item.label}</div>
                <div style={{ fontSize: "0.75rem", opacity: 0.65 }}>{item.detail}</div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {allDone && (
        <p style={{ margin: "10px 0 0", color: "#3ECFA0", fontWeight: 700, fontSize: "0.82rem" }}>
          All checkpoints complete. {isClaimedToday ? "XP awarded and streak updated." : "Applying rewards..."}
        </p>
      )}
    </SpotlightCard>
  );
}

import { Trash2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

/**
 * MealList component showing logged meals for today.
 */
export default function MealList({ todayMeals, deleteMeal }) {
  return (
    <div className="meal-list-container">
      <h3 style={{ margin: "0 0 15px 0", opacity: 0.8 }}>
        Today's Log ({todayMeals.length})
      </h3>

      {todayMeals.length === 0 ? (
        <p style={{ opacity: 0.6, fontStyle: "italic" }}>
          Nothing logged yet! Scan a meal below to start.
        </p>
      ) : (
        <div className="meal-list-scroll">
          <AnimatePresence>
            {["Breakfast", "Lunch", "Dinner", "Snacks"].map((cat) => {
              const catMeals = todayMeals.filter((m) => m.category === cat);
              if (catMeals.length === 0) return null;
              return (
                <motion.div
                  key={cat}
                  initial={{ opacity: 0, x: -10 }}
                  animate={{ opacity: 1, x: 0 }}
                  style={{ marginBottom: "16px" }}
                >
                  <div className="category-header">
                    <span className="category-dot"></span>
                    {cat}
                  </div>
                  {catMeals.map((meal) => (
                    <motion.div
                      key={meal.id}
                      className="glass-panel meal-list-item hover-lift"
                      layout
                    >
                      <div>
                        <p style={{ margin: 0, fontWeight: "bold" }}>
                          {meal.title}
                        </p>
                        <p
                          style={{
                            margin: "4px 0 0",
                            fontSize: "0.8rem",
                            opacity: 0.8,
                          }}
                        >
                          {meal.protein}g P · {meal.carbs}g C · {meal.fat}g F
                        </p>
                      </div>
                      <div
                        style={{
                          display: "flex",
                          alignItems: "center",
                          gap: "15px",
                        }}
                      >
                        <p
                          style={{
                            margin: 0,
                            fontWeight: "800",
                            color: "var(--primary-coral)",
                          }}
                        >
                          {meal.calories} kcal
                        </p>
                        <button
                          onClick={() => deleteMeal(meal.id)}
                          className="delete-btn"
                        >
                          <Trash2 size={16} />
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </motion.div>
              );
            })}
          </AnimatePresence>
        </div>
      )}
    </div>
  );
}

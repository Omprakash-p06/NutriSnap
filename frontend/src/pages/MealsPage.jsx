import { useMealHistory } from "../hooks/useMealHistory";
import MealList from "../components/dashboard/MealList";
import HydrationWidget from "../components/dashboard/HydrationWidget";

export default function MealsPage() {
  const { todayMeals, deleteMeal } = useMealHistory();

  return (
    <div className="page-meals">
      <div className="page-meals__header">
        <h1 className="page-title">My Meals Today</h1>
        <p className="page-subtitle">
          {todayMeals.length === 0
            ? "No meals logged yet — scan something!"
            : `${todayMeals.length} meal${todayMeals.length > 1 ? "s" : ""} logged`}
        </p>
      </div>

      <div className="page-meals__content">
        <section className="clay-card clay-card--wide">
          <MealList todayMeals={todayMeals} deleteMeal={deleteMeal} />
        </section>

        <section className="clay-card clay-card--wide" style={{ marginTop: "20px" }}>
          <HydrationWidget />
        </section>
      </div>
    </div>
  );
}

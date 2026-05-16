import { useMealHistory } from "../hooks/useMealHistory";
import MealList from "../components/dashboard/MealList";
import HydrationWidget from "../components/dashboard/HydrationWidget";

export default function MealsPage() {
  const { todayMeals, deleteMeal } = useMealHistory();

  return (
    <div className="page-container page-meals max-w-4xl mx-auto pt-6 px-4">
      <div className="text-center mb-10 mt-6">
        <h1 className="text-4xl font-bold text-white tracking-tight mb-2">My Meals Today</h1>
        <p className="text-gray-400 text-lg">
          {todayMeals.length === 0
            ? "No meals logged yet — scan something!"
            : `${todayMeals.length} meal${todayMeals.length > 1 ? "s" : ""} logged`}
        </p>
      </div>

      <div className="flex flex-col gap-6">
        <section className="glass-panel w-full">
          <MealList todayMeals={todayMeals} deleteMeal={deleteMeal} />
        </section>

        <section className="glass-panel w-full">
          <HydrationWidget />
        </section>
      </div>
    </div>
  );
}

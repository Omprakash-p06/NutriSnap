import { DashboardPage } from "./DashboardPage";

export default function PlannerPage() {
  return (
    <div className="page-planner">
      <div className="page-planner__header">
        <h1 className="page-title">Meal Planner</h1>
        <p className="page-subtitle">AI-generated meal plan tailored to your goals</p>
      </div>
      <DashboardPage />
    </div>
  );
}

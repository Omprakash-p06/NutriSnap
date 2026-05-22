import React from "react";
import { X } from "lucide-react";

export const RecipeModal = ({ recipe, onClose, isLoading = false, error = null }) => {
  if (!recipe && !isLoading) return null;

  const nutrition = recipe?.nutrition || {};
  const calories = nutrition.calories ?? recipe?.calories;
  const protein = nutrition.protein ?? recipe?.protein;
  const carbs = nutrition.carbs ?? recipe?.carbs;
  const fat = nutrition.fat ?? recipe?.fat;
  const servings = recipe?.servings;
  const timeMinutes = recipe?.time_minutes;

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close-button" onClick={onClose}>
          <X size={24} />
        </button>
        <h2>{recipe?.name || "Recipe Details"}</h2>
        {recipe?.summary ? <p>{recipe.summary}</p> : recipe?.why ? <p>{recipe.why}</p> : null}
        {servings || timeMinutes ? (
          <p className="modal-meta">
            {servings ? `Servings: ${servings}` : "Servings: -"} · {timeMinutes ? `Time: ${timeMinutes} min` : "Time: -"}
          </p>
        ) : null}

        {isLoading ? (
          <p>Loading recipe details...</p>
        ) : (
          <>
            {error ? <p className="modal-error">{error}</p> : null}
            {recipe?.ingredients && recipe.ingredients.length > 0 ? (
              <>
                <h3>Ingredients</h3>
                <ul>
                  {recipe.ingredients.map((ing, i) => (
                    <li key={i}>{ing}</li>
                  ))}
                </ul>
              </>
            ) : (
              <p>Recipe details are not available for this suggestion yet.</p>
            )}
            {recipe?.steps && recipe.steps.length > 0 ? (
              <>
                <h3>Steps</h3>
                <ol>
                  {recipe.steps.map((step, i) => (
                    <li key={i}>{step}</li>
                  ))}
                </ol>
              </>
            ) : null}
          </>
        )}

        <h3>Nutrition</h3>
        <p>Calories: {calories ?? "-"}</p>
        <p>Protein: {protein ?? "-"}g</p>
        <p>Carbs: {carbs ?? "-"}g</p>
        <p>Fat: {fat ?? "-"}g</p>
      </div>
    </div>
  );
};

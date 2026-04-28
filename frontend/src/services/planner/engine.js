export function filterByCalories(recipes, calorieGap) {
  if (!calorieGap || calorieGap <= 0) return [];
  // Allow recipes that fit within the gap, or slightly exceed it (10% buffer)
  return recipes.filter(r => r.calories <= calorieGap * 1.1);
}

export function scoreByMacros(recipes, gaps) {
  const needsHighProtein = gaps.protein && gaps.protein > 20;

  return recipes.map(recipe => {
    let score = 0;
    
    // Exact macro fit heuristic (higher score for matching gaps)
    if (gaps.protein && recipe.protein <= gaps.protein) {
      score += recipe.protein * 2; // Protein is weighted heavier
    }
    if (gaps.carbs && recipe.carbs <= gaps.carbs) {
      score += recipe.carbs;
    }
    if (gaps.fat && recipe.fat <= gaps.fat) {
      score += recipe.fat;
    }

    // High protein priority
    if (needsHighProtein) {
      const isHighProtein = recipe.tags && recipe.tags.includes("high-protein");
      const highRatio = (recipe.protein / recipe.calories) > 0.1;
      
      if (isHighProtein || highRatio) {
        score += 1000; // Large boost to guarantee priority
      }
    }

    return { ...recipe, _score: score };
  }).sort((a, b) => b._score - a._score);
}

export function selectTop(recipes, count = 3) {
  return recipes.slice(0, count).map(r => {
    const copy = { ...r };
    delete copy._score;
    return copy;
  });
}

export function suggestMeals(recipes, gaps) {
  if (!recipes || !recipes.length) return [];
  if (!gaps || !gaps.calories) return recipes.slice(0, 3); // Fallback
  
  const calorieFiltered = filterByCalories(recipes, gaps.calories);
  const scored = scoreByMacros(calorieFiltered, gaps);
  return selectTop(scored, 3);
}

import React from 'react';
import { motion } from 'framer-motion';

export const RecipeCard = ({ recipe }) => {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-white rounded-xl overflow-hidden shadow-sm border border-gray-100 flex flex-col h-full"
    >
      <div 
        className="h-32 bg-gray-200 bg-cover bg-center"
        style={{ backgroundImage: `url(${recipe.image})` }}
      />
      <div className="p-4 flex-1 flex flex-col">
        <h4 className="font-semibold text-gray-900 mb-1">{recipe.name}</h4>
        <div className="flex flex-wrap gap-1 mb-3">
          {recipe.tags && recipe.tags.slice(0, 2).map(tag => (
            <span key={tag} className="px-2 py-0.5 bg-indigo-50 text-indigo-600 text-xs rounded-full">
              {tag}
            </span>
          ))}
        </div>
        <div className="mt-auto pt-3 border-t border-gray-50 flex justify-between items-end">
          <div>
            <p className="text-xs text-gray-500 uppercase tracking-wider">Calories</p>
            <p className="font-medium text-gray-900">{recipe.calories} kcal</p>
          </div>
          <div className="text-right">
            <p className="text-xs text-gray-500 uppercase tracking-wider">Protein</p>
            <p className="font-medium text-emerald-600">{recipe.protein}g</p>
          </div>
        </div>
      </div>
    </motion.div>
  );
};

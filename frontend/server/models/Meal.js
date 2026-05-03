import mongoose from "mongoose";

const mealSchema = new mongoose.Schema({
  userEmail: {
    type: String,
    required: true,
    index: true, // Ensures speedy querying by user bucket
  },
  title: {
    type: String,
    required: true,
  },
  calories: {
    type: Number,
    required: true,
  },
  protein: {
    type: Number,
    required: true,
  },
  carbs: {
    type: Number,
    required: true,
  },
  fat: {
    type: Number,
    required: true,
  },
  multiplier: {
    type: Number,
    default: 1,
  },
  category: {
    type: String,
    enum: ["Breakfast", "Lunch", "Dinner", "Snacks"],
    default: "Snacks",
  },
  timestamp: {
    type: Date,
    default: Date.now,
  },
});

export default mongoose.model("Meal", mealSchema);

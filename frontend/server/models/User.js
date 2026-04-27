import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true
  },
  dailyCalorieGoal: {
    type: Number,
    default: 2000
  },
  proteinGoal: {
    type: Number,
    default: 150
  },
  carbsGoal: {
    type: Number,
    default: 200
  },
  fatGoal: {
    type: Number,
    default: 70
  },
  streak: {
    type: Number,
    default: 0
  },
  lastLogDate: {
    type: String, // ISO date string YYYY-MM-DD for easy comparison
    default: null
  }
});

export default mongoose.model('User', userSchema);

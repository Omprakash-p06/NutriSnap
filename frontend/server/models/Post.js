import mongoose from 'mongoose';

const postSchema = new mongoose.Schema({
  userEmail: { type: String, required: true },
  userName: { type: String, required: true },
  userAvatar: { type: String },
  mealName: { type: String, required: true },
  calories: { type: Number },
  imageUrl: { type: String }, // Base64 or cloud URL
  likes: { type: Number, default: 0 },
  timestamp: { type: Date, default: Date.now }
});

export default mongoose.model('Post', postSchema);

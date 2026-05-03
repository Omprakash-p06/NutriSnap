import mongoose from "mongoose";

const waterLogSchema = new mongoose.Schema({
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: "User",
    required: true,
  },
  amount: {
    type: Number, // in ml
    required: true,
  },
  timestamp: {
    type: Date,
    default: Date.now,
  },
});

// Index for quick queries of today's water
waterLogSchema.index({ userId: 1, timestamp: -1 });

export default mongoose.model("WaterLog", waterLogSchema);

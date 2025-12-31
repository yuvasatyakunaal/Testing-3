import mongoose from "mongoose";

const detailsSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
  },
  roll: {
    type: Number,
    required: true,
    unique: true,
  },
  branch: {
    type: String,
    required: true,
  },
  skills: {
    type: [String],
    required: true,
  },
});

export const details = mongoose.model("details", detailsSchema);
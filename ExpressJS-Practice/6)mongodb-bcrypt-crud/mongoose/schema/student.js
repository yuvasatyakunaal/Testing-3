import mongoose from "mongoose";

const studentSchema = new mongoose.Schema({
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
  cgpas: {
    type: [Number],
    required: true,
  },
  secretPassword: {
    type: String,
    required: true,
    unique: true,
  },
});

export const Students = mongoose.model("Students", studentSchema);

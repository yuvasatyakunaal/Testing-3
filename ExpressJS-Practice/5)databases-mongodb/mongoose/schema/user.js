import mongoose from "mongoose";

const userSchema = new mongoose.Schema({
  name: {
    type: String,
    required: true,
    unique: true,
  },
  mainName: {
    type: String,
  },
  password: {
    type: String,
    required: true,
  },
});

export const user = mongoose.model("User", userSchema);

import express from "express";
import dotenv from "dotenv";
import cors from "cors";
import mongoose from "mongoose";
import detailsRouter from './routes/details.js'

const app = express();
dotenv.config();

// CORS (must when doing with both frontend and backend with different origins)
app.use(
  cors({
    origin: process.env.FRONTEND_URL,
  })
);
mongoose.connect(process.env.MONGO_URL)
.then(() => console.log("Connected to database"))
.catch((err) => console.log(`Error : ${err}`));

app.use(express.json());

app.use(detailsRouter);

app.get("/", (req, res) => {
  res.status(200).send({ message: "Welcome to my world!" });
});

const port = process.env.PORT || 3000;
app.listen(port, () => {
  console.log(`----------------------------------`);
  console.log(`Running on http://localhost:${port}/`);
  console.log(`----------------------------------`);
});

import express from "express";
import dotenv from "dotenv";
import mongoose from "mongoose";
import studentRouter from "./routes/students.js";

const app = express();

// Dotnev config
dotenv.config();

// To handle json data in express
app.use(express.json());

// Mongodb connection
mongoose
  .connect(process.env.MONGO_URL)
  .then(() => {
    console.log("Connected to database\n");
  })
  .catch((err) => {
    console.log(`Error while connecting to database : ${err}\n`);
  });

// Get all routes from a specified destination
app.use(studentRouter);

// Home : showing what and how to use
app.get("/", (req, res) => {
  res.status(200).send({
    message: "Handling data with Express + MongoDB = CRUD",
    availableRoutes: {
      POST: {
        "/api/student": "Add a new student (requires JSON body)",
      },
      GET: {
        "/api/student": "Get all students",
        "/api/student/roll/:roll": "Get a student by roll number",
        "/api/student/secret/:secretPassword":
          "Get a student by their secret password (hashed with bcrypt)",
      },
      PUT: {
        "/api/student/:roll": "Update ALL details of a student (full object)",
      },
      PATCH: {
        "/api/student/:roll": "Update PARTIAL details of a student",
      },
      DELETE: {
        "/api/student/:roll": "Delete a student by roll number",
      },
    },
    usageNote:
      "Use Thunder Client or Postman to test the API with appropriate HTTP methods and JSON data",
  });
});

const port = process.env.PORT || 3001;
app.listen(port, () => {
  console.log(
    `----------------------------------
Running on http://localhost:${port}/
----------------------------------`
  );
});

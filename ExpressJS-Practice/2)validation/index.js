import express from "express";
import dotenv from "dotenv";
import {
  query,
  validationResult,
  body,
  matchedData,
  checkSchema,
} from "express-validator";
import { createValidationSchema } from "./utils/validationSchema.js";

const app = express();
const port = process.env.PORT || 3000;

// configurations
dotenv.config();
// Middlewares
app.use(express.json());

// Inputs
const users = [
  { id: 101, name: "user1", mainName: "User101" },
  { id: 102, name: "user2", mainName: "User102" },
  { id: 103, name: "user3", mainName: "User103" },
  { id: 104, name: "user4", mainName: "User104" },
];

app.get("/", (req, res) => {
  res.status(200).send("<h3>Welcome to my world</h3>");
});

app.get(
  "/api/users",
  query("filter")
    .isString()
    .notEmpty()
    .withMessage("Must not be empty")
    .isLength({ min: 4, max: 4 })
    .withMessage("Must be of exactly 4 characters"),
  (req, res) => {
    const result = validationResult(req);
    console.log("-----\n", result);
    const {
      query: { filter, value },
    } = req;
    if (filter && value) {
      return res.send(users.filter((user) => user[filter].includes(value)));
    } else {
      return res.send(users);
    }
  }
);

// Instead of keeping all inside api, we can create seperate schema and use it here...
app.post("/api/users", checkSchema(createValidationSchema), (req, res) => {
  const result = validationResult(req);
  // If result is empty, it means there are not errors occurred
  if (!result.isEmpty()) {
    return res.status(400).send({ Errors: result.array() });
  }
  const data = matchedData(req);
  const newUser = { id: users[users.length - 1].id + 1, ...data };
  users.push(newUser);
  return res.status(200).send(data);
});

app.listen(port, () => {
  console.log(
    `-------------------------------\nRunning on http://localhost:${port}/\n-------------------------------`
  );
});
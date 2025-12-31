import { Router } from "express";
import {
  query,
  validationResult,
  checkSchema,
  matchedData,
} from "express-validator";
import { createValidationSchema } from "../utils/validationSchema.js";
import resolveIndexByUserId from "../middleware/resolveIndex.js";
import users from "../inputs/users.js";
import { user } from "../mongoose/schema/user.js";

const router = Router();

router.get(
  "/api/users",
  query("filter")
    .isString()
    .notEmpty()
    .withMessage("Must not be empty")
    .isLength({ min: 4, max: 4 })
    .withMessage("Must be of exactly 4 characters"),
  (req, res) => {
    // Gets same session id as the id which we got in "/" path
    console.log(req.session.id);
    req.sessionStore.get(req.session.id, (err, sessionData) => {
      if (err) {
        console.log(err);
        throw err;
      }
      console.log(sessionData);
    });
    const result = validationResult(req);
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

// MongoDB storing...
router.post(
  "/api/users",
  checkSchema(createValidationSchema),
  async (req, res) => {
    const result = validationResult(req);
    if (!result.isEmpty()) {
      return res.send(result.array());
    }

    const data = matchedData(req);
    console.log(data);
    // const { body } = req;
    const newUser = new user(data);
    try {
      const savedUser = await newUser.save();
      return res.status(200).send(savedUser);
    } catch (err) {
      console.log(`Error : ${err}`);
      return res.sendStatus(401);
    }
  }
);

// -----
router.put("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const { body, findUserIndex } = req;
  users[findUserIndex] = { id: users[findUserIndex].id, ...body };
  return res.sendStatus(200);
});

router.patch("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const { body, findUserIndex } = req;
  users[findUserIndex] = { ...users[findUserIndex], ...body };
  return res.sendStatus(200);
});

router.delete("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const { findUserIndex } = req;
  users.splice(findUserIndex, 1); // Deletes the first element of found index
  res.sendStatus(200);
});

export default router;

import express from "express";
import dotenv from "dotenv";
import session from "express-session";
import routes from "./routers/index.js";

import users from "./inputs/users.js";

const app = express();

dotenv.config();
app.use(express.json());

// session (must be before routes)
app.use(
  session({
    secret: "kunaal the coder",
    saveUninitialized: false,
    resave: false,
    cookie: { maxAge: 60000 * 60 * 2 }, // 60000 means 60 seconds, 60000 * 60 means 1 hour, 60000 * 60 * 2 means 2 hours, this cookie will be valid till 2 hours.
  })
);

// Getting all user routers using this middleware
app.use(routes);

const port = process.env.PORT || 3000;

// Starting page route
app.get("/", (req, res) => {
  console.log(req.session);
  console.log(`id = ${req.session.id}\n-----`);
  req.session.visited = true; // To do not take the different session id's
  res.status(200).send({ message: "Welcome to my world !" });
});

// To get more knowledge about sessions using a simple auth example type
app.post("/api/auth", (req, res) => {
  const {
    body: { name, password },
  } = req;
  const findUser = users.find((user) => user.name === name);
  if (!findUser || findUser.password !== password) {
    return res.status(401).send({ message: "BAD CREDENTIALS" });
  }

  req.session.user = findUser;
  return res.status(200).send(findUser);
});

app.get("/api/auth/status", (req, res) => {
  return req.session.user ? res.status(200).send(req.session.user) : res.status(401).send({ message: "NOT AUTHENTICATED" });
})

// Listening
app.listen(port, () => {
  console.log(
    `----------------------------------
Running on http://localhost:${port}/
----------------------------------`
  );
});

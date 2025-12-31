import express from "express";
import dotenv from "dotenv";
import session from "express-session";
import passport from "passport";
import routes from "./routers/index.js";
import mongoose from "mongoose";
import "./strategies/local-strategy.js";

import users from "./inputs/users.js";

const app = express();

// Mongoose connection with local MongoDB compass URL (connection string)
mongoose
  .connect("mongodb://localhost/express_mongoose")    // inside the localhost, express_mongoose folder will be created and inside it the database will be there.
  .then(() => console.log("Connected to DataBase\n"))
  .catch((err) => console.log(`Error : ${err}`));

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

// Passport package initialization and session (Middleware)
app.use(passport.initialize());
app.use(passport.session());

// Getting all user routers using this middleware
app.use(routes);

const port = process.env.PORT || 3000;

app.get("/", (req, res) => {
  res.status(200).send({message : "Welcome to my world !"});
})

app.post("/api/auth", passport.authenticate("local"), (req, res) => {
  res.status(200).send({ message: "Login successful", user: req.user });
});

app.get("/api/auth/status", (req, res) => {
  console.log(`Inside api/auth/status endpoint`);
  console.log(req.user);
  console.log(req.session);
  return req.user ? res.status(200).send(req.user) : res.sendStatus(401);
});

app.post("/api/auth/logout", (req, res) => {
  if (!req.user) {
    return res.sendStatus(401);
  }
  req.logout((err) => {
    if (err) {
      return res.sendStatus(401);
    }
    return res.status(200).send({ message: "Logged out" });
  });
});

// Listening
app.listen(port, () => {
  console.log(
    `----------------------------------
Running on http://localhost:${port}/
----------------------------------`
  );
});

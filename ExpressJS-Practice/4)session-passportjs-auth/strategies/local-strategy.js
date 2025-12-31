import passport from "passport";
import { Strategy } from "passport-local";
import users from "../inputs/users.js";

passport.serializeUser((user, done) => {
  console.log("------\nInside Serialize user");
  console.log(user);
  done(null, user.id); // or done(null, user.name);
});

passport.deserializeUser((id, done) => {
  console.log("Inside Deserialize user");
  console.log(`Deserializing user id = ${id}`);
  try {
    const findUser = users.find((user) => user.id === id);
    // or const findUser = users.find((user) => user.name === name);
    if (!findUser) {
      throw new Error("User not found");
    }
    done(null, findUser);
  } catch (err) {
    done(err, null);
  }
});

export default passport.use(
  new Strategy(
    { usernameField: "name", passwordField: "password" },
    (name, password, done) => {
      try {
        const findUser = users.find((user) => user.name === name);
        if (!findUser) {
          return done(null, false, { message: "User not found" });
        }
        if (findUser.password !== password) {
          return done(null, false, { message: "Invalid password" });
        }
        return done(null, findUser);
      } catch (err) {
        return done(err);
      }
    }
  )
);

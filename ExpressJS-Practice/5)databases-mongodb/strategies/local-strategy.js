import passport from "passport";
import { Strategy } from "passport-local";
import users from "../inputs/users.js";
import { user } from "../mongoose/schema/user.js";

passport.serializeUser((user, done) => {
  console.log("------\nInside Serialize user");
  console.log(user);
  done(null, user.id); // or done(null, user.name);
});

passport.deserializeUser(async (id, done) => {
  console.log("Inside Deserialize user");
  console.log(`Deserializing user id = ${id}`);
  try {
    const findUser = await user.findById(id);
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
    async (name, password, done) => {
      try {
        const findUser = await user.findOne({ name });
        if (!findUser) {
          throw new Error("User not found");
        }
        if (findUser.password !== password) {
          throw new Error("Invalid credentials");
        }
        return done(null, findUser);
      } catch (err) {
        return done(err);
      }
    }
  )
);

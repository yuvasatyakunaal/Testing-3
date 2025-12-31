import express, { response } from "express";
import dotenv from "dotenv";

// .env config for accessing environment variables
dotenv.config();

// object (app) for class (express)
const app = express();

// Adding middleware for parsing JSON (if this is not there POST,PUT parsing of JSON wont happen)
app.use(express.json());

// Middleware (custom)
// Use this where you want inside the routes, before the req, res things
// Steps : URL -> middleware -> middleware (if exist)... -> (req,res) - method 
const resolveIndexByUserId = (req, res, next) => {
  const {params : { id }} = req;
  const parseId = parseInt(id);
  if (isNaN(parseId)) {
    return res.sendStatus(400);
  }

  const findUserIndex = users.findIndex((user) => user.id == parseId);

  // If user not found
  if (findUserIndex == -1) {
    return res.sendStatus(404);
  }

  req.findUserIndex = findUserIndex;
  next();
}

// Writing like this will be used by all the routes present below this line, or else keep inside the API before req,res method
// app.use(resolveIndexByUserId);

const port = process.env.PORT || 3000;

const users = [
  { id: 101, name: "user1", displayName: "User1" },
  { id: 102, name: "user2", displayName: "User2" },
  { id: 103, name: "user3", displayName: "User3" },
];

const products = [
  { id: 201, name: "Chicken Fried rice", price: 15.5 },
  { id: 202, name: "Chicken Manchuria", price: 20.5 },
  { id: 203, name: "Veg Noodles", price: 10.99 },
  { id: 203, name: "Veg Fried rice", price: 7.05 },
];

// -- GET --
// Routes (home)
app.get("/", (req, res) => {
  res.status(200);
  res.send({ name: "kunaaaal" });
});

// Route (/api/users)
app.get("/api/users", (req, res) => {
  res.status(200);
  res.send(users);
});

// Route Params
app.get("/api/users/:id", (req, res) => {
  console.log(req.params);
  const parsedId = parseInt(req.params.id);
  if (isNaN(parsedId)) {
    return res.status(400).send({ message: "Bad request. Invalid ID" });
  }
  const findUser = users.find((user) => user.id == parsedId);
  if (!findUser) {
    return res.sendStatus(404);
  }
  return res.send(findUser);
});

// Query Params
app.get("/api/products", (req, res) => {
  res.status(200);

  const { filter, value } = req.query;
  if (filter && value) {
    // Filters based on finding the substring given as query parameter
    // i.e.., ?filter=name&value=rice => return all products consisting of substring = rice
    return res.send(
      products.filter((product) =>
        product[filter].toLowerCase().includes(value)
      )
    );
  } else {
    return res.send(products);
  }
});

// -- POST --
app.post("/api/users", (req, res) => {
  const body = req.body;
  const newUser = { id: users[users.length - 1].id + 1, ...body };
  users.push(newUser);
  return res.status(200).send(newUser);
});

// -- PUT --
// For this we cannot only give the key what we want to change, but also every other keys inside JSON like
// { "name" : "hahaha", "displayName" : "User1"} for keeping parameter as 101 for id.
// Becuase for PUT, it overwrites everything how you gave...
app.put("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const {body, findUserIndex} = req;
  users[findUserIndex] = { id: users[findUserIndex].id, ...body };
  return res.sendStatus(200);
});

// -- PATCH --
// For this we can only give the key what we want to change inside JSON like
// { "name" : "hahaha"} for keeping parameter as 101 for id.
// Becuase for PATCH, it overwrites only the key which u mentioned...
app.patch("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const {body, findUserIndex} = req;
  users[findUserIndex] = { ...users[findUserIndex], ...body };
  return res.sendStatus(200);
});

// -- DELETE --
app.delete("/api/users/:id", resolveIndexByUserId, (req, res) => {
  const {findUserIndex} = req;
  users.splice(findUserIndex, 1); // Deletes the first element of found index
  res.sendStatus(200);
});


// Listening to express app
app.listen(port, () => {
  console.log(
    `----------------------------------\nRunning on http://localhost:${port}/\n----------------------------------`
  );
});

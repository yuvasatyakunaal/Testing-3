import { Router } from "express";
import { details } from "../mongoose/schema/detailsSchema.js";

const router = Router();

router.get("/api/data", (req, res) => {
  res.status(200).send({ message: "Welcome." });
});

router.post("/api/data", async (req, res) => {
  const { body } = req;
  console.log(body);
  if (!Object.keys(body).length) {
    return res.status(400).send({ message: "Data is empty" });
  }
  const newDetails = new details(body);
  try {
    const savedDetails = await newDetails.save();
    console.log("Saved to database successfully");
    return res
      .status(200)
      .send({ message: "Saved to database successfully", savedDetails });
  } catch (err) {
    console.log("Something went wrong", err.message);
    return res.status(401).send({ message: "Something went wrong" });
  }
});

export default router;

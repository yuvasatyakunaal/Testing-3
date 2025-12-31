import { Router } from "express";
import { validationResult, matchedData, checkSchema } from "express-validator";
import bcrypt from "bcrypt";
import { Students } from "../mongoose/schema/student.js";
import { studentValidationSchema } from "../utils/validation.js";
import { hashSecretPassword } from "../utils/hashing.js";

const router = Router();

// -- POST --
router.post(
  "/api/student",
  checkSchema(studentValidationSchema),
  async (req, res) => {
    const result = validationResult(req);
    if (!result.isEmpty()) {
      return res.status(400).send(result.array());
    }

    const data = matchedData(req);
    // hashing the secretPassword
    data.secretPassword = hashSecretPassword(data.secretPassword);
    console.log(data);

    const newStudent = new Students(data);
    try {
      const savedStudents = await newStudent.save();
      res.status(200).send(savedStudents);
    } catch (err) {
      console.log(`Error : ${err}`);
      res.sendStatus(401);
    }
  }
);

// -- GET (all) --
router.get("/api/student", async (req, res) => {
  try {
    // Gets all students without secretPassword field
    const allStudents = await Students.find({}).select("-secretPassword");
    res.status(200).send(allStudents);
  } catch (err) {
    console.log(`Error : ${err}`);
    res.sendStatus(400);
  }
});

// -- GET (one - roll) --
router.get("/api/student/roll/:roll", async (req, res) => {
  const {
    params: { roll },
  } = req;
  try {
    const student = await Students.findOne({ roll: roll }).select(
      "-secretPassword"
    );
    if (!student) {
      return res.status(400).send({ message: `${roll} : Student not found` });
    }
    return res.status(200).send({ student: student });
  } catch (err) {
    console.log(`Error : ${err}`);
    res.status(500).send({ message: "Something went wrong" });
  }
});

// -- GET (one - secretPassword) --
// for roll - 160122771031, secretPassword = kunmeg2431
// for roll - 160122771059, secretPassword = water
// for roll - 160122771063, secretPassword = shiva
router.get("/api/student/secret/:secretPassword", async (req, res) => {
  const {
    params: { secretPassword },
  } = req;
  try {
    const allStudents = await Students.find({});
    if (!allStudents) {
      return res.status(400).send({ message: "Student not Found" });
    }
    for (const student of allStudents) {
      const match = await bcrypt.compare(
        secretPassword,
        student.secretPassword
      );
      if (match) {
        const studentObj = student.toObject(); // convert to plain object
        delete studentObj.secretPassword; // remove the sensitive field
        return res.status(200).send({ student: studentObj });
      }
    }
    res.status(404).send({ message: "Secret Password doesn't exist" });
  } catch (err) {
    console.log(`Error : ${err}`);
    res.status(500).send({ message: "Something went wrong" });
  }
});

// -- PUT (complete object) --
router.put("/api/student/:roll", async (req, res) => {
  const {
    params: { roll },
  } = req;
  const updatingCompleteData = req.body;

  try {
    const updatedStudent = await Students.findOneAndUpdate(
      { roll: roll },
      updatingCompleteData,
      { new: true }
    ).select("-secretPassword");
    if (!updatedStudent) {
      return res.status(400).send({ message: `${roll} : Student not found` });
    }
    return res.status(200).send({ message: "Student details updated" });
  } catch (err) {
    console.log(`Error : ${err}`);
    res.status(500).send({ message: "Something went wrong" });
  }
});

// -- PATCH (partial object) --
router.patch("/api/student/:roll", async (req, res) => {
  const {
    params: { roll },
  } = req;
  const updatingPartialData = req.body;
  try {
    const updatedStudent = await Students.findOneAndUpdate(
      { roll: roll },
      updatingPartialData,
      { new: true }
    );
    if (!updatedStudent) {
      return res.status(400).send({ message: `${roll} : Student not found` });
    }
    return res.status(200).send({ message: "Student details updated" });
  } catch (err) {
    console.log(`Error : ${err}`);
    res.status(500).send({ message: "Something went wrong" });
  }
});

// -- DELETE (one) --
router.delete("/api/student/:roll", async (req, res) => {
  const {
    params: { roll },
  } = req;
  try {
    const deleted = await Students.findOneAndDelete({ roll: roll });
    if (!deleted) {
      return res.status(400).send({ message: `${roll} : Student not found` });
    }
    return res
      .status(200)
      .send({ message: "Student deleted", student: deleted });
  } catch (err) {
    console.log(`Error : ${err}`);
    res.status(500).send({ message: "Something went wrong" });
  }
});

export default router;

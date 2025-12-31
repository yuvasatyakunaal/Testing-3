import { Router } from "express";
import userRouter from "./users.js";
import productRouter from "./products.js";

const router = Router();

router.use(userRouter);
router.use(productRouter);

export default router;
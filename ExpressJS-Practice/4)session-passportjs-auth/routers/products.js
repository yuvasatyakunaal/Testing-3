import { Router } from "express";
import products from "../inputs/products.js";

const router = Router();

router.get("/api/products", (req, res) => {
  res.status(200);
  const { filter, value } = req.query;
  if (filter && value) {
    return res.send(
      products.filter((product) =>
        product[filter].toLowerCase().includes(value)
      )
    );
  } else {
    return res.send(products);
  }
});

export default router;
const express = require("express");
const app = express();
app.use(express.json());
  

const restaurants = [
  { id: 1, name: "Campus Cafe", cuisine: "Continental" },
  { id: 2, name: "Spice Corner", cuisine: "Indian" },
  { id: 3, name: "Noodle House", cuisine: "Chinese" }
];

// GET all restaurants
app.get("/api/restaurants", (req, res) => {
  res.json(restaurants);
});

// GET one restaurant by id
app.get("/api/restaurants/:id", (req, res) => {
  const restaurant = restaurants.find(r => r.id === Number(req.params.id));
  if (!restaurant) {
    return res.status(404).json({ error: "Restaurant not found" });
  }
  res.json(restaurant);
});

app.listen(3000, () => console.log("listening on 3000"));

//from kaushik
//from bharath
//from Ayushgi
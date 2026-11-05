// server.js -- the CampusEats Catalogue REST API (Node + Express)
const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());            // read JSON request bodies
app.use(express.static('public'));  // serve the web page

// the menu -- in memory for now (a real database comes in Lecture 10)
// Seeded with 4 items as requested in Step 2
let items = [
  { id: 1, name: 'Veg Thali',   price: 90, available: true },
  { id: 2, name: 'Paneer Roll', price: 70, available: true },
  { id: 3, name: 'Cold Coffee', price: 40, available: true },
  { id: 4, name: 'Masala Dosa', price: 80, available: false }
];
let nextId = 5;

// GET /items  -- list the whole menu (returns 200 OK)
app.get('/items', (req, res) => {
  res.status(200).json(items);
});

// GET /items/:id  -- one dish, or 404 if absent
app.get('/items/:id', (req, res) => {
  const item = items.find(i => i.id === Number(req.params.id));
  if (!item) return res.status(404).json({ error: 'not found' });
  res.status(200).json(item);
});

// POST /items  -- add a dish (validates required fields, reply 422 if missing, 201 on success)
app.post('/items', (req, res) => {
  const { name, price, available } = req.body;
  if (!name || typeof name !== 'string' || name.trim() === '') {
    return res.status(422).json({ error: 'name required' });
  }
  if (price === undefined || price === null || isNaN(Number(price)) || Number(price) <= 0) {
    return res.status(422).json({ error: 'valid positive price required' });
  }

  const item = {
    id: nextId++,
    name: name.trim(),
    price: Number(price),
    available: available !== undefined ? Boolean(available) : true
  };

  items.push(item);
  res.status(201).json(item);
});

if (require.main === module) {
  app.listen(PORT, () => console.log(`Catalogue on http://localhost:${PORT}`));
}

module.exports = app;

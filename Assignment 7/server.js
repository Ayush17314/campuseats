// server.js — Apollo Server 4 over Express with MySQL Resolvers
// Exposes GraphQL endpoint at /graphql and serves the frontend client at /

const express = require('express');
const http = require('http');
const path = require('path');
const fs = require('fs');
const cors = require('cors');
const { ApolloServer } = require('@apollo/server');
const { expressMiddleware } = require('@apollo/server/express4');
const db = require('./db');

const typeDefs = fs.readFileSync(path.join(__dirname, 'schema.graphql'), 'utf-8');

const resolvers = {
  Query: {
    // List all dishes with optional filtering (category, available)
    dishes: async (_, { category, available }) => {
      let sql = 'SELECT id, name, price, available, category, description FROM dishes WHERE 1=1';
      const params = [];

      if (category !== undefined && category !== null) {
        sql += ' AND category = ?';
        params.push(category);
      }
      if (typeof available === 'boolean') {
        sql += ' AND available = ?';
        params.push(available);
      }

      sql += ' ORDER BY id ASC';
      const [rows] = await db.query(sql, params);
      return rows.map(row => ({
        id: String(row.id),
        name: row.name,
        price: Number(row.price),
        available: Boolean(row.available),
        category: row.category,
        description: row.description
      }));
    },

    // Fetch a single dish by ID (maps to WHERE id = ?)
    dish: async (_, { id }) => {
      const sql = 'SELECT id, name, price, available, category, description FROM dishes WHERE id = ?';
      const [rows] = await db.query(sql, [id]);
      if (!rows || rows.length === 0) return null;
      const row = rows[0];
      return {
        id: String(row.id),
        name: row.name,
        price: Number(row.price),
        available: Boolean(row.available),
        category: row.category,
        description: row.description
      };
    }
  },

  Mutation: {
    // Add a new dish to the catalogue (maps to INSERT INTO dishes)
    addDish: async (_, { input }) => {
      const { name, price, available = true, category = 'General', description = null } = input;
      const sql = 'INSERT INTO dishes (name, price, available, category, description) VALUES (?, ?, ?, ?, ?)';
      const [result] = await db.query(sql, [name, price, available, category, description]);

      const insertId = result.insertId;
      const [rows] = await db.query('SELECT id, name, price, available, category, description FROM dishes WHERE id = ?', [insertId]);
      const row = rows[0];
      return {
        id: String(row.id),
        name: row.name,
        price: Number(row.price),
        available: Boolean(row.available),
        category: row.category,
        description: row.description
      };
    },

    // Update an existing dish in the catalogue (maps to UPDATE dishes WHERE id = ?)
    updateDish: async (_, { id, input }) => {
      const [existing] = await db.query('SELECT id, name, price, available, category, description FROM dishes WHERE id = ?', [id]);
      if (!existing || existing.length === 0) {
        throw new Error(`Dish with id ${id} not found.`);
      }
      const current = existing[0];
      const name = input.name !== undefined ? input.name : current.name;
      const price = input.price !== undefined ? input.price : current.price;
      const available = input.available !== undefined ? input.available : current.available;
      const category = input.category !== undefined ? input.category : current.category;
      const description = input.description !== undefined ? input.description : current.description;

      const sql = 'UPDATE dishes SET name = ?, price = ?, available = ?, category = ?, description = ? WHERE id = ?';
      await db.query(sql, [name, price, available, category, description, id]);

      const [updated] = await db.query('SELECT id, name, price, available, category, description FROM dishes WHERE id = ?', [id]);
      const row = updated[0];
      return {
        id: String(row.id),
        name: row.name,
        price: Number(row.price),
        available: Boolean(row.available),
        category: row.category,
        description: row.description
      };
    }
  }
};

async function startServer() {
  const app = express();
  const httpServer = http.createServer(app);

  const server = new ApolloServer({
    typeDefs,
    resolvers,
  });

  await server.start();

  // Middleware pipeline
  app.use(cors());
  app.use(express.json());

  // Apollo GraphQL Endpoint
  app.use('/graphql', expressMiddleware(server));

  // Serve static HTML/CSS demonstration frontend
  app.use(express.static(path.join(__dirname, 'public')));

  const PORT = process.env.PORT || 4000;
  httpServer.listen(PORT, () => {
    console.log(`====================================================`);
    console.log(`🚀 CampusEats Catalogue GraphQL Service is running!`);
    console.log(`🌐 Web Client UI:   http://localhost:${PORT}/`);
    console.log(`📡 GraphQL Endpoint: http://localhost:${PORT}/graphql`);
    console.log(`====================================================`);
  });
}

if (require.main === module) {
  startServer().catch(err => {
    console.error('Fatal error starting server:', err);
  });
}

module.exports = { startServer, typeDefs, resolvers };

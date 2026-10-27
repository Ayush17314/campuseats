// db.js — MySQL Database Connection with mysql2/promise
// Supports live MySQL connections and a transparent fallback for standalone testing.

require('dotenv').config();
const mysql = require('mysql2/promise');

const config = {
  host: process.env.DB_HOST || 'localhost',
  user: process.env.DB_USER || 'root',
  password: process.env.DB_PASSWORD || '',
  database: process.env.DB_NAME || 'campuseats',
  port: Number(process.env.DB_PORT) || 3306,
  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0
};

let pool = null;
let useFallback = false;

// In-memory fallback dataset (matching schema.sql exactly) if MySQL server is not running
const fallbackDishes = [
  { id: 1, name: 'Paneer Tikka Roll', price: 90.0, available: true, category: 'Rolls', description: 'Grilled cottage cheese wrapped in fresh wheat paratha with mint chutney' },
  { id: 2, name: 'Veg Dum Biryani', price: 130.0, available: true, category: 'Rice', description: 'Aromatic basmati rice cooked with fresh seasonal vegetables and spices' },
  { id: 3, name: 'Masala Dosa', price: 65.0, available: true, category: 'South Indian', description: 'Crisp rice crepe stuffed with tempered mashed potatoes, served with sambar' },
  { id: 4, name: 'Cold Coffee Frappe', price: 45.0, available: false, category: 'Beverages', description: 'Chilled blended milk coffee topped with chocolate syrup' }
];
let nextId = 5;

try {
  pool = mysql.createPool(config);
} catch (err) {
  console.warn('⚠️ [db.js] Failed to initialize mysql2 pool:', err.message);
  useFallback = true;
}

/**
 * Executes a query against MySQL or the simulated fallback store.
 * @param {string} sql 
 * @param {Array} params 
 * @returns {Promise<Array>} [rows, fields]
 */
async function query(sql, params = []) {
  if (!useFallback && pool) {
    try {
      const [rows] = await pool.query(sql, params);
      return [rows];
    } catch (err) {
      const isConnError =
        err.name === 'AggregateError' ||
        err.code === 'ECONNREFUSED' ||
        err.code === 'ER_BAD_DB_ERROR' ||
        err.code === 'ENOTFOUND' ||
        err.code === 'ETIMEDOUT' ||
        err.code === 'EACCES' ||
        (err.errors && Array.isArray(err.errors));

      if (isConnError) {
        if (!useFallback) {
          console.warn(`⚠️ [db.js] MySQL server unavailable on ${config.host}:${config.port}. Activating local in-memory fallback.`);
          useFallback = true;
        }
      } else {
        throw err;
      }
    }
  }

  // --- Fallback In-Memory Engine for Standalone Demonstration ---
  const normalizedSql = sql.trim().toUpperCase();

  // 1. SELECT by ID
  if (normalizedSql.includes('WHERE ID =') || normalizedSql.includes('WHERE `ID` =')) {
    const id = Number(params[0]);
    const dish = fallbackDishes.find(d => d.id === id);
    return [dish ? [{ ...dish }] : []];
  }

  // 2. SELECT all with optional category / available filters
  if (normalizedSql.startsWith('SELECT')) {
    let result = [...fallbackDishes];
    let paramIdx = 0;
    if (sql.includes('category = ?')) {
      const cat = params[paramIdx++];
      result = result.filter(d => d.category.toLowerCase() === String(cat).toLowerCase());
    }
    if (sql.includes('available = ?')) {
      const avail = Boolean(params[paramIdx++]);
      result = result.filter(d => Boolean(d.available) === avail);
    }
    return [result];
  }

  // 3. INSERT INTO dishes
  if (normalizedSql.startsWith('INSERT INTO')) {
    const [name, price, available, category, description] = params;
    const newDish = {
      id: nextId++,
      name: String(name),
      price: Number(price),
      available: available !== undefined ? Boolean(available) : true,
      category: category ? String(category) : 'General',
      description: description ? String(description) : null
    };
    fallbackDishes.push(newDish);
    return [{ insertId: newDish.id, affectedRows: 1 }];
  }

  // 4. UPDATE dishes
  if (normalizedSql.startsWith('UPDATE')) {
    const id = Number(params[params.length - 1]);
    const dish = fallbackDishes.find(d => d.id === id);
    if (!dish) return [{ affectedRows: 0 }];

    // Simple parser for standard UPDATE pattern
    if (params.length === 6) {
      const [name, price, available, category, description] = params;
      if (name !== undefined) dish.name = String(name);
      if (price !== undefined) dish.price = Number(price);
      if (available !== undefined) dish.available = Boolean(available);
      if (category !== undefined) dish.category = String(category);
      if (description !== undefined) dish.description = String(description);
    }
    return [{ affectedRows: 1 }];
  }

  return [[]];
}

module.exports = {
  query,
  pool,
  isUsingFallback: () => useFallback
};

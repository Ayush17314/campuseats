/**
 * CS543 Assignment 8 REST API Test Suite
 * Validates GET /items, GET /items/:id (with 404), POST /items (201 & 422 validation)
 */

const http = require('http');
const app = require('./server');

const PORT = 3088;
let server;

function request(method, path, body = null) {
  return new Promise((resolve, reject) => {
    const payload = body ? JSON.stringify(body) : null;
    const req = http.request({
      hostname: '127.0.0.1',
      port: PORT,
      path: path,
      method: method,
      headers: {
        'Accept': 'application/json',
        ...(payload ? {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload)
        } : {})
      }
    }, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          resolve({ status: res.statusCode, body: JSON.parse(data) });
        } catch {
          resolve({ status: res.statusCode, body: data });
        }
      });
    });
    req.on('error', reject);
    if (payload) req.write(payload);
    req.end();
  });
}

async function run() {
  console.log('Testing CampusEats Catalogue REST API (Assignment 8)...');
  let failures = 0;

  function expect(condition, name) {
    if (condition) {
      console.log(`  ✓ ${name}`);
    } else {
      console.error(`  ✗ ${name}`);
      failures++;
    }
  }

  // 1. GET /items (List)
  const listRes = await request('GET', '/items');
  expect(listRes.status === 200, 'GET /items returns HTTP 200');
  expect(Array.isArray(listRes.body) && listRes.body.length === 4, 'GET /items returns 4 seed records');

  // 2. GET /items/1 (Fetch one existing)
  const oneRes = await request('GET', '/items/1');
  expect(oneRes.status === 200, 'GET /items/1 returns HTTP 200');
  expect(oneRes.body.name === 'Veg Thali', 'GET /items/1 returns correct dish data');

  // 3. GET /items/999 (Fetch non-existent -> 404)
  const notFoundRes = await request('GET', '/items/999');
  expect(notFoundRes.status === 404, 'GET /items/999 returns HTTP 404');
  expect(notFoundRes.body.error === 'not found', 'GET /items/999 error body is "not found"');

  // 4. POST /items without name -> 422
  const missingNameRes = await request('POST', '/items', { price: 50 });
  expect(missingNameRes.status === 422, 'POST /items without name returns HTTP 422');

  // 5. POST /items without price -> 422
  const missingPriceRes = await request('POST', '/items', { name: 'Samosa' });
  expect(missingPriceRes.status === 422, 'POST /items without price returns HTTP 422');

  // 6. POST /items with valid data -> 201 Created
  const createRes = await request('POST', '/items', { name: 'Chole Bhature', price: 95, available: true });
  expect(createRes.status === 201, 'POST /items returns HTTP 201 Created');
  expect(createRes.body.id === 5 && createRes.body.name === 'Chole Bhature', 'POST /items returns new dish with id: 5');

  // 7. GET /items/5 -> 200
  const fetchNewRes = await request('GET', '/items/5');
  expect(fetchNewRes.status === 200, 'GET /items/5 returns HTTP 200');
  expect(fetchNewRes.body.name === 'Chole Bhature', 'GET /items/5 returns newly created dish');

  // 8. GET /items reflects updated count
  const listAfterRes = await request('GET', '/items');
  expect(listAfterRes.body.length === 5, 'GET /items now returns 5 dishes');

  server.close(() => {
    if (failures === 0) {
      console.log('\nAll tests passed successfully (8/8)!');
      process.exit(0);
    } else {
      console.error(`\n${failures} tests failed!`);
      process.exit(1);
    }
  });
}

server = app.listen(PORT, run);

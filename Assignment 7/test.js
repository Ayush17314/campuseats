// test.js — Automated verification of Assignment 7 GraphQL server, queries, and mutations

const http = require('http');
const { startServer } = require('./server');

function makeRequest(path, options = {}, body = null) {
  return new Promise((resolve, reject) => {
    const req = http.request({
      hostname: 'localhost',
      port: 4000,
      path,
      method: options.method || 'GET',
      headers: options.headers || {}
    }, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, data, headers: res.headers }));
    });
    req.on('error', reject);
    if (body) req.write(typeof body === 'string' ? body : JSON.stringify(body));
    req.end();
  });
}

async function runTests() {
  console.log('🧪 Starting Assignment 7 Verification Test Suite...\n');

  // Start the server
  await startServer();
  await new Promise(r => setTimeout(r, 1000));

  // 1. Test Static Frontend Page
  console.log('1️⃣ Testing Frontend Page (GET /)...');
  const frontRes = await makeRequest('/');
  if (frontRes.status === 200 && frontRes.data.includes('CampusEats')) {
    console.log('   ✅ PASS: Frontend index.html served correctly (HTTP 200).');
  } else {
    throw new Error(`Frontend failed with status ${frontRes.status}`);
  }

  // 2. Test GraphQL Query: dishes (initial seed data)
  console.log('\n2️⃣ Testing Initial Query: { dishes { id name price available } }...');
  const queryAll = `
    query {
      dishes {
        id
        name
        price
        available
      }
    }
  `;
  const qRes = await makeRequest('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, { query: queryAll });

  const qJson = JSON.parse(qRes.data);
  if (qJson.data && qJson.data.dishes && qJson.data.dishes.length >= 4) {
    console.log(`   ✅ PASS: Initial query returned ${qJson.data.dishes.length} dishes:`);
    qJson.data.dishes.forEach(d => console.log(`      - #${d.id}: ${d.name} (₹${d.price}) [Available: ${d.available}]`));
  } else {
    throw new Error('Initial query did not return expected seed dishes: ' + JSON.stringify(qJson));
  }

  // 3. Test GraphQL Query: dish(id: 1)
  console.log('\n3️⃣ Testing Single Item Query: { dish(id: 1) { id name price } }...');
  const queryOne = `
    query {
      dish(id: "1") {
        id
        name
        price
      }
    }
  `;
  const oneRes = await makeRequest('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, { query: queryOne });

  const oneJson = JSON.parse(oneRes.data);
  if (oneJson.data && oneJson.data.dish && oneJson.data.dish.name === 'Paneer Tikka Roll') {
    console.log(`   ✅ PASS: Query by ID returned dish #${oneJson.data.dish.id}: ${oneJson.data.dish.name}`);
  } else {
    throw new Error('Query by ID failed: ' + JSON.stringify(oneJson));
  }

  // 4. Test GraphQL Mutation: addDish (as specified in PDF)
  console.log('\n4️⃣ Testing Mutation: addDish(input: { name: "Paneer Roll", price: 90 }) (from PDF)...');
  const mutationAdd = `
    mutation {
      addDish(input: { name: "Paneer Roll", price: 90, category: "Rolls", available: true }) {
        id
        name
        price
        available
      }
    }
  `;
  const mRes = await makeRequest('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, { query: mutationAdd });

  const mJson = JSON.parse(mRes.data);
  if (mJson.data && mJson.data.addDish && mJson.data.addDish.name === 'Paneer Roll') {
    console.log(`   ✅ PASS: Mutation succeeded! Created dish:`);
    console.log(`      - ID: #${mJson.data.addDish.id}`);
    console.log(`      - Name: ${mJson.data.addDish.name}`);
    console.log(`      - Price: ₹${mJson.data.addDish.price}`);
  } else {
    throw new Error('Mutation failed: ' + JSON.stringify(mJson));
  }

  // 5. Verify Mutation Persistence in Subsequent Query
  console.log('\n5️⃣ Verifying Updated Catalogue (Live After Mutation)...');
  const postRes = await makeRequest('/graphql', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  }, { query: queryAll });

  const postJson = JSON.parse(postRes.data);
  const found = postJson.data.dishes.find(d => d.name === 'Paneer Roll');
  if (found) {
    console.log(`   ✅ PASS: Newly added dish is present in dishes list (Total items: ${postJson.data.dishes.length}).`);
  } else {
    throw new Error('Newly added dish not found in subsequent query!');
  }

  console.log('\n🎉 ALL ASSIGNMENT 7 VERIFICATION TESTS PASSED SUCCESSFULLY!\n');
  process.exit(0);
}

runTests().catch(err => {
  console.error('\n❌ Test Suite Failed:', err);
  process.exit(1);
});

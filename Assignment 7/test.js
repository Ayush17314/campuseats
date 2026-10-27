// test.js — Automated verification of Assignment 7 GraphQL server, schema, and resolvers
// Uses Apollo Server 4's executeOperation API for fast, robust in-process testing.

const fs = require('fs');
const path = require('path');
const { ApolloServer } = require('@apollo/server');
const { typeDefs, resolvers } = require('./server');

async function runTests() {
  console.log('🧪 Starting Assignment 7 Verification Test Suite...\n');

  // Initialize Apollo Server instance
  const server = new ApolloServer({
    typeDefs,
    resolvers,
  });
  await server.start();
  console.log('✅ Apollo Server 4 initialized and started successfully.\n');

  // 1. Verify static frontend index.html exists and is well-formed
  console.log('1️⃣ Verifying Frontend Page (public/index.html)...');
  const htmlPath = path.join(__dirname, 'public', 'index.html');
  if (fs.existsSync(htmlPath)) {
    const htmlContent = fs.readFileSync(htmlPath, 'utf-8');
    if (htmlContent.includes('CampusEats') && htmlContent.includes('addDishForm') && htmlContent.includes('/graphql')) {
      console.log('   ✅ PASS: public/index.html exists and contains CampusEats form and GraphQL caller.');
    } else {
      throw new Error('index.html is missing required markup components.');
    }
  } else {
    throw new Error('public/index.html not found.');
  }

  // 2. Test Initial GraphQL Query: dishes (initial seed data)
  console.log('\n2️⃣ Testing Initial Query: { dishes { id name price available category } }...');
  const queryAll = `
    query {
      dishes {
        id
        name
        price
        available
        category
      }
    }
  `;
  const qRes = await server.executeOperation({ query: queryAll });
  const qData = qRes.body.singleResult.data;

  if (qData && qData.dishes && qData.dishes.length >= 4) {
    console.log(`   ✅ PASS: Initial query returned ${qData.dishes.length} dishes:`);
    qData.dishes.forEach(d => console.log(`      - #${d.id}: ${d.name} (₹${d.price}) [Category: ${d.category}, Available: ${d.available}]`));
  } else {
    throw new Error('Initial query failed: ' + JSON.stringify(qRes.body.singleResult));
  }

  // 3. Test GraphQL Query: dish(id: 1) (Maps to WHERE id = ?)
  console.log('\n3️⃣ Testing Single Item Query: { dish(id: "1") { id name price } }...');
  const queryOne = `
    query GetDish($id: ID!) {
      dish(id: $id) {
        id
        name
        price
        available
      }
    }
  `;
  const oneRes = await server.executeOperation({
    query: queryOne,
    variables: { id: "1" }
  });
  const oneData = oneRes.body.singleResult.data;

  if (oneData && oneData.dish && oneData.dish.name === 'Paneer Tikka Roll') {
    console.log(`   ✅ PASS: Query by ID returned dish #${oneData.dish.id}: ${oneData.dish.name} (₹${oneData.dish.price})`);
  } else {
    throw new Error('Query by ID failed: ' + JSON.stringify(oneRes.body.singleResult));
  }

  // 4. Test GraphQL Mutation: addDish (as explicitly shown in Assignment 7 PDF)
  console.log('\n4️⃣ Testing Mutation: addDish(input: { name: "Paneer Roll", price: 90 }) (from PDF)...');
  const mutationAdd = `
    mutation AddDish($input: AddDishInput!) {
      addDish(input: $input) {
        id
        name
        price
        available
        category
      }
    }
  `;
  const mRes = await server.executeOperation({
    query: mutationAdd,
    variables: {
      input: {
        name: "Paneer Roll",
        price: 90,
        category: "Rolls",
        description: "Fresh cottage cheese roll with spices",
        available: true
      }
    }
  });
  const mData = mRes.body.singleResult.data;

  if (mData && mData.addDish && mData.addDish.name === 'Paneer Roll') {
    console.log(`   ✅ PASS: Mutation succeeded! Created record via INSERT:`);
    console.log(`      - ID: #${mData.addDish.id}`);
    console.log(`      - Name: ${mData.addDish.name}`);
    console.log(`      - Price: ₹${mData.addDish.price}`);
    console.log(`      - Available: ${mData.addDish.available}`);
  } else {
    throw new Error('Mutation failed: ' + JSON.stringify(mRes.body.singleResult));
  }

  // 5. Verify Mutation Persistence in Subsequent Query
  console.log('\n5️⃣ Verifying Updated Catalogue (Live After Mutation)...');
  const postRes = await server.executeOperation({ query: queryAll });
  const postData = postRes.body.singleResult.data;
  const found = postData.dishes.find(d => d.name === 'Paneer Roll');

  if (found) {
    console.log(`   ✅ PASS: Newly added dish is present in dishes list (Total items: ${postData.dishes.length}).`);
  } else {
    throw new Error('Newly added dish not found in subsequent query!');
  }

  // 6. Test Non-Null Schema Validation (! sign)
  console.log('\n6️⃣ Testing Schema Non-Null Validation (omitting required "price")...');
  const badMutation = `
    mutation {
      addDish(input: { name: "Incomplete Dish" }) {
        id
      }
    }
  `;
  const badRes = await server.executeOperation({ query: badMutation });
  if (badRes.body.singleResult.errors && badRes.body.singleResult.errors.length > 0) {
    console.log('   ✅ PASS: GraphQL schema correctly rejected mutation missing non-null field price: Float!');
    console.log(`      - Error: ${badRes.body.singleResult.errors[0].message}`);
  } else {
    throw new Error('Schema validation failed to catch missing required field!');
  }

  console.log('\n======================================================');
  console.log('🎉 ALL ASSIGNMENT 7 VERIFICATION TESTS PASSED (100%)');
  console.log('======================================================\n');
  process.exit(0);
}

runTests().catch(err => {
  console.error('\n❌ Test Suite Failed:', err);
  process.exit(1);
});

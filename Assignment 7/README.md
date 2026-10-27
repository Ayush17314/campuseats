# CampusEats — Catalogue Service in GraphQL (Assignment 7)
# Team Submission:** TeamID 03  

**Course:** CS543 Web Services  
**Assignment:** Assignment 7   
**Instructor:** Dr. Pramit Mazumdar, IIIT Vadodara  

## Team Members

| Name | Roll Number | Assignment Responsibility |
| :--- | :--- | :--- |
| **Ayush Kumar Dubey** | 20251651030 | Apollo Server & Express Setup (`schema.graphql`, `schema.sql `) |
| **Abhinav Jain** | 20251651003 | Database Connection & mysql2 Pool (`db.js`) |
| **Anuj Gupta** | 20251651025 | Catalogue Service Schema & SQL (`HTML/CSS- Frontend`) |
| **Bharath Kumar MP** | 20251651031 | Query & Mutation Resolvers (` server.js `)|
| **Kaushik Nanda Upadhaya** | 20251651050 | Demonstration Web Frontend (`public/index.html`) & Evidence |

---

## One-Line Run Instruction

```bash
npm install express && npm start
```

* **Interactive Web Demonstration UI:** [http://localhost:4000/](http://localhost:4000/)
* **Apollo GraphQL API Endpoint / Sandbox:** [http://localhost:4000/graphql](http://localhost:4000/graphql)

---

## Demonstration Video & Screenshots

* **Google Drive Demonstration Video:** `https://drive.google.com/drive/folders/1zaFwqUmAzhQJ82glMnFP7RDZWmgDILNz?usp=sharing` 

* **Github Link for complete working:** `https://github.com/Ayush17314/CampusEats30`

* **Screenshot 1 (Before Mutation — Initial Query State):** Located in [`Before mutation.png`](Before mutation.png)
* **Screenshot 2 (After Mutation — Live Mutation & Instant Refresh):** Located in [`After mutation.png`](After mutation.png)

---

## Answers to Required Assignment Questions

### 1. Which CampusEats service did you pick?
We picked the **Catalogue Service** (specifically the **Menu / Dishes** entity). In the CampusEats microservice architecture (established in Assignment 2), the Catalogue service exclusively owns restaurants, menus, dishes, prices, and food item availability. Exposing this service via GraphQL allows clients (e.g., student mobile app or cafeteria display) to query only the exact fields they need (e.g., just `name` and `price` for quick menu rendering, or full details including `description` and `available`) in a single network round-trip.

### 2. Name one field a client can skip and one it cannot (why we use the "!" sign).
* **Field a client cannot skip:** `name: String!` (and `price: Float!`) in `AddDishInput` (as well as `id: ID!` on `Dish`).  
  **Why:** The exclamation mark `!` in GraphQL Schema Definition Language (SDL) designates a **Non-Null** constraint. If a client attempts to execute the `addDish` mutation without providing the `name` or `price`, the GraphQL execution engine halts the request and returns a schema validation error before the resolver function is ever invoked.
* **Field a client can skip:** `description: String` (and `category: String`, `available: Boolean`).  
  **Why:** Because these fields omit the `!` symbol, they are **Nullable**. A client can omit them from the mutation payload or query, and GraphQL allows the request. The resolver safely applies sensible defaults (e.g., `available: true`, `category: "General"`, `description: null`).

### 3. Map it to SQL/other database: which part of your query became the WHERE, and which resolver ran the INSERT?
* **Which part became the WHERE:**  
  In the GraphQL queries:
  - `dish(id: ID!)`: The query argument `id` maps directly into the SQL `WHERE id = ?` clause:
    ```sql
    SELECT id, name, price, available, category, description FROM dishes WHERE id = ?;
    ```
  - `dishes(category: String, available: Boolean)`: The optional query filter arguments map dynamically into:
    ```sql
    SELECT id, name, price, available, category, description FROM dishes WHERE 1=1 AND category = ? AND available = ?;
    ```
* **Which resolver ran the INSERT:**  
  The mutation resolver **`Mutation.addDish`** in [`server.js`](server.js) executed the SQL `INSERT` statement:
  ```sql
  INSERT INTO dishes (name, price, available, category, description) VALUES (?, ?, ?, ?, ?);
  ```
  It receives the `input` arguments from the GraphQL mutation payload, issues the `INSERT` via `db.query()`, captures the newly generated `insertId`, and executes a follow-up `SELECT` to return the freshly inserted dish record matching the requested selection set.

---

## Deliverables Checklist

- [x] **`schema.graphql`**: Contains object type `Dish`, queries `dishes` (list) & `dish` (by ID), inputs, and mutation `addDish`.
- [x] **`server.js` + `db.js`**: Apollo Server 4 over Express with working SQL resolvers via `mysql2/promise` (with automatic standalone fallback).
- [x] **`schema.sql`**: Complete MySQL DDL with table definition and 4 realistic seed rows.
- [x] **`public/index.html`**: Interactive web page using `fetch()` to query and mutate GraphQL data live with before/after visualization.
- [x] **`README.md`**: Run command, Team 03 names and roll numbers, video/screenshot links, and answers to all 3 questions.

# CampusEats — Catalogue Service as a REST API (Assignment 8)
## Team Submission: TeamID 03

**Course:** CS543 Web Services  
**Assignment:** Assignment 8 of 12  
**Instructor:** Dr. Pramit Mazumdar, IIIT Vadodara  

---

## Team Members

| Name | Roll Number |
| :--- | :--- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

---

## One-Line Run Instruction

```bash
npm install && npm start
```

* **Interactive Web Demonstration UI:** [http://localhost:3000/](http://localhost:3000/)
* **REST Endpoints:**
  * `GET` `/items` — List all dishes
  * `GET` `/items/:id` — Fetch one dish
  * `POST` `/items` — Add a new dish

---

## Demonstration Video & Screenshots

* **Google Drive Demonstration Video:** `https://drive.google.com/drive/folders/1zaFwqUmAzhQJ82glMnFP7RDZWmgDILNz?usp=sharing`
* **Screenshot 1 (Before POST — Initial State with Seed Records):** [`Before POST.png`](Before%20POST.png)
* **Screenshot 2 (After POST — Live Dish Added & Table Refreshed):** [`After POST.png`](After%20POST.png)

---

## Answers to Required Assignment Questions

### 1. Which CampusEats service did you pick, and what are its routes (method + path)?

We picked the **CampusEats Menu / Catalogue Service**. In our CampusEats platform, the Catalogue service acts as the source of truth for all food items, dishes, prices, and availability.

The service exposes the following REST routes:

| HTTP Method | Route Path | Description |
| :--- | :--- | :--- |
| `GET` | `/items` | Retrieves the list of all dishes currently in the catalogue. |
| `GET` | `/items/:id` | Fetches a single dish by its numeric ID (`req.params.id`). Returns 404 if not found. |
| `POST` | `/items` | Creates a new dish from the incoming JSON payload (`req.body`) and adds it to the menu. |

---

### 2. Which status codes did you return, and for which outcomes (200 / 201 / 404 / 422)?

We returned standard HTTP status codes corresponding to the semantic outcome of each operation:

* **`200 OK`**:
  * Returned on **`GET /items`** when the list of all menu items is successfully retrieved.
  * Returned on **`GET /items/:id`** when the item matching the requested ID is found.
* **`201 Created`**:
  * Returned on **`POST /items`** when a new dish passes validation, is assigned a new ID, is added to the in-memory array, and is returned to the client.
* **`404 Not Found`**:
  * Returned on **`GET /items/:id`** when no item exists in the array with the requested ID (e.g. `GET /items/999`).
* **`422 Unprocessable Content`**:
  * Returned on **`POST /items`** when the payload is missing mandatory fields (e.g. `name` is omitted or empty, or `price` is omitted or non-numeric).

---

### 3. Where did you use `req.params` and where `req.body`? Why does POST need `express.json()`?

* **Where `req.params` was used:**  
  In **`GET /items/:id`**, where `req.params.id` extracts the URL path parameter. We convert it to a number with `Number(req.params.id)` to look up the item in our array.

* **Where `req.body` was used:**  
  In **`POST /items`**, where `req.body` provides the JSON object sent by the client containing `{ name, price, available }`.

* **Why POST needs `express.json()`:**  
  By default, Node.js streams incoming HTTP request bodies as raw chunks of binary data (`Buffer`). Express does not automatically parse request body streams, so `req.body` is `undefined`.  
  The built-in middleware `express.json()` intercepts requests with a `Content-Type: application/json` header, buffers the incoming stream data, parses the raw JSON string into a JavaScript object, and populates `req.body`. Without `app.use(express.json())`, accessing `req.body.name` or destructuring `const { name, price } = req.body` would throw a runtime `TypeError: Cannot destructure property 'name' of 'req.body' as it is undefined`.

---

## Deliverables Checklist

- [x] **`server.js`**: Express REST API with `GET /items`, `GET /items/:id`, and `POST /items`.
- [x] **`package.json`**: With `express` dependency and run scripts.
- [x] **`public/index.html` + `public/style.css`**: Frontend that fetches and renders menu items, plus a form that POSTs new records and refreshes the view.
- [x] **`test.js`**: Integration test covering all 8 assertions and HTTP status codes.
- [x] **`Before POST.png` + `After POST.png`**: Screenshots demonstrating before and after adding a record live.
- [x] **`README.md`**: Team 03 info, run command, Drive link, and full answers to all 3 questions.

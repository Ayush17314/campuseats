# CampusEats

CampusEats is a CS543 coursework repository for Group 3. It contains a small Express API used for HTTP exercises and the design artefacts for a campus food-ordering system.

## Team

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

## Run the API

Install dependencies, then start the local server:

```bash
npm install
node server.js
```

The API listens on `http://localhost:3000` and returns an in-memory restaurant catalogue.

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/api/restaurants` | Returns all restaurants. |
| `GET` | `/api/restaurants/:id` | Returns one restaurant, or a `404` JSON response when the ID does not exist. |

## Repository contents

| Path | Description |
| --- | --- |
| `server.js` | Express implementation of the sample restaurant API. |
| `package.json` / `package-lock.json` | Node.js package metadata and locked dependencies. |
| `Assignment1/` | HTTP-by-hand evidence, browser network analysis, and the CampusEats brief. |
| `Assignment2/` | CampusEats service design, database schema, diagrams, and task reports. |

See the README in each assignment directory for an itemized description of its deliverables.

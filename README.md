# CampusEats

CampusEats is a CS543 coursework repository for Group 3. It contains a small Express API used for HTTP exercises and the design artefacts for a campus food-ordering system.

## TeamID 03

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
| `Assignment 1/` | HTTP-by-hand evidence, browser network analysis, and the CampusEats brief. |
| `Assignment 2/` | CampusEats service design, database schema, diagrams, and task reports. |
| `Assignment 3/` | Integrate an External SOAP Partner into CampusEats at the contract level. |
| `Assignment 4/` | REST architectural constraints and Richardson Maturity Model analysis. |
| `Assignment 5/` | CampusEats Orders microservice with OpenAPI contracts. |
| `Assignment 6/` | Status codes, RFC 7807 Problem Details, payload validation & XML negotiation. |
| `Assignment 7/` | CampusEats Catalogue Service in GraphQL with Apollo Server & MySQL. |
| `Assignment 8/` | CampusEats Catalogue Service as a REST API with Node & Express. |

See the README in each assignment directory for an itemized description of its deliverables.

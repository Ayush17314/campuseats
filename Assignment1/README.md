## TeamID 03

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

# Assignment 1 — HTTP and Network Analysis

This assignment documents the HTTP behaviour of the local CampusEats Express API and examines how a production website loads in a browser.

## Files

| File | Description |
| --- | --- |
| `brief.md` | CampusEats product brief defining users, core domain concepts, service boundaries, and key operations. |
| `http-log.md` | Five annotated `curl` request/response examples for the local API, including successful `GET` and `HEAD` requests and a deliberate `404` case. |
| `network-analysis.md` | Chrome DevTools Network-panel analysis of a Crunchyroll page load, covering request counts, transfer sizes, timings, redirects, and third-party resources. |

## Local API used for the HTTP log

From the repository root, run:

```bash
npm install
node server.js
```

The server listens on `http://localhost:3000`.

| Endpoint | Result |
| --- | --- |
| `GET /api/restaurants` | Returns the full in-memory restaurant list. |
| `GET /api/restaurants/:id` | Returns a restaurant by ID. |
| `HEAD /api/restaurants/:id` | Returns response headers without a body. |
| `GET /api/restaurants/999` | Demonstrates the API's `404 Not Found` response. |

## Tools used

- Node.js and Express
- `curl`
- Chrome DevTools Network panel
- Git and GitHub

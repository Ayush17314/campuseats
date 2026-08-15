# HTTP by Hand — Request/Response Log

**API used:** My own read-only JSON API, built with Express, running locally at
`http://localhost:3000`. Serves a small in-memory list of restaurants.

---

## Request 1 — GET all restaurants

curl.exe -i http://localhost:3000/api/restaurants

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 156

[{"id":1,"name":"Campus Cafe","cuisine":"Continental"},{"id":2,"name":"Spice Corner","cuisine":"Indian"},{"id":3,"name":"Noodle House","cuisine":"Chinese"}]

**Note:** 200 OK means the request succeeded. Content-Type: application/json tells the client to parse the body as JSON.

---

## Request 2 — GET restaurant with id 1

curl.exe -i http://localhost:3000/api/restaurants/1

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 53

{"id":1,"name":"Campus Cafe","cuisine":"Continental"}

**Note:** 200 OK — this specific resource (id 1) exists and was returned.

---

## Request 3 — GET restaurant with id 2

curl.exe -i http://localhost:3000/api/restaurants/2

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 49

{"id":2,"name":"Spice Corner","cuisine":"Indian"}

**Note:** Same as above — confirms the API behaves consistently across different ids.

---

## Request 4 — HEAD request, headers only

curl.exe -I http://localhost:3000/api/restaurants/1

HTTP/1.1 200 OK
Content-Type: application/json; charset=utf-8
Content-Length: 53

**Note:** -I sends a HEAD request — same headers as a normal GET, but curl never downloads the body. Useful for checking a resource exists without fetching all its data.

---

## Request 5 — deliberate 404 (required failure case)

curl.exe -i http://localhost:3000/api/restaurants/999

HTTP/1.1 404 Not Found
Content-Type: application/json; charset=utf-8
Content-Length: 32

{"error":"Restaurant not found"}

**Note:** 404 Not Found — id 999 doesn't exist in the restaurants list. My own code (the `if (!restaurant)` check in server.js) is what generates this response.

---

## Status code / Content-Type cheat sheet

| Code                           | Meaning here                                                    |
|--------------------------------|-----------------------------------------------------------------|
| 200 OK                         | Request succeeded, body contains the requested data             |
| 404 Not Found                  | The requested restaurant id doesn't exist                       |
| Content-Type: application/json | Body is JSON — safe to parse with `res.json()` / `JSON.parse()` |
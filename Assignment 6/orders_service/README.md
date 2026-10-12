# CampusEats Orders Service — Assignment 5 & Assignment 6

## TeamID 03

| Name | Roll no. |
| --- | --- |
| Ayush Kumar Dubey | 20251651030 |
| Abhinav Jain | 20251651003 |
| Anuj Gupta | 20251651025 |
| Bharath Kumar MP | 20251651031 |
| Kaushik Nanda Upadhaya | 20251651050 |

## Run

```powershell
python -m pip install -r requirements.txt
```

In one PowerShell window, start the Payments service stand-in:

```powershell
python payments_stub.py
```

In a second PowerShell window, start Orders:

```powershell
$env:PAYMENTS_BASE_URL = "http://127.0.0.1:5001"
python app.py
```

`PAYMENTS_BASE_URL` is required and must point to Payments. The client sends `POST /charges` with `orderId`, `amountMinorUnits`, `cardToken`, and the incoming `Idempotency-Key` header.

## Verify

```powershell
python -m openapi_spec_validator openapi.yaml
pytest -q
```

Run the commands in [`transcript.txt`](transcript.txt) against the running Orders and Payments services to reproduce the full `curl -i` transcript covering the happy path, all RFC 7807 Problem Details failure paths, XML/JSON content negotiation, and Assignment 5 idempotency/caching checks.

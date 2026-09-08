# CampusEats Orders Service

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

In one PowerShell window, start the Tutorial 4 Payments service. If it is not
available locally, the included development stand-in lets you exercise the
real HTTP boundary:

```powershell
python payments_stub.py
```

In a second PowerShell window, start Orders:

```powershell
$env:PAYMENTS_BASE_URL = "http://127.0.0.1:5001"
python app.py
```

`PAYMENTS_BASE_URL` is required and must point to Payments. The client sends
`POST /charges` with `orderId`, `amountMinorUnits`, `cardToken`, and the
incoming `Idempotency-Key` header.

## Verify

```powershell
npx.cmd --yes @redocly/cli lint openapi.yaml
pytest -q
```

Run the commands in [CURL_TRANSCRIPT.md](CURL_TRANSCRIPT.md) against a running Payments service to capture the required `-i` evidence.

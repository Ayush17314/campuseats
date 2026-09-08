# CampusEats Orders Service

## Run

```powershell
python -m pip install -r requirements.txt
$env:PAYMENTS_BASE_URL = "http://127.0.0.1:5001"
python app.py
```

`PAYMENTS_BASE_URL` must point to the Tutorial 4 Payments service. The client sends `POST /charges` with `orderId`, `amountMinorUnits`, `cardToken`, and the incoming `Idempotency-Key` header.

## Verify

```powershell
npx.cmd --yes @redocly/cli lint openapi.yaml
pytest -q
```

Run the commands in [CURL_TRANSCRIPT.md](CURL_TRANSCRIPT.md) against a running Payments service to capture the required `-i` evidence.

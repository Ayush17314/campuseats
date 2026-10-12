# Local CampusEats Payments Service

This is a small local-only dependency used to demonstrate the Assignment 4 Orders service's outbound HTTP call. It is not part of the Orders-service submission folder.

## Run

From `E:\campuseats\Assignment 4\payments_service`, with the same virtual environment active:

```powershell
python -m pip install -r requirements.txt
python app.py
```

It listens on `http://127.0.0.1:5001` and accepts `POST /charges`. It returns an approved transaction for `tok_demo`; use `tok_declined` to return HTTP 402.

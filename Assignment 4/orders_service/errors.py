from flask import Response, jsonify


def problem(status: int, title: str, detail: str, type_: str | None = None) -> Response:
    """The one RFC-7807-inspired error representation used throughout the API."""
    body = {
        "type": type_ or f"https://campuseats.example/problems/{title.lower().replace(' ', '-')}",
        "title": title,
        "status": status,
        "detail": detail,
    }
    response = jsonify(body)
    response.status_code = status
    response.content_type = "application/problem+json"
    return response

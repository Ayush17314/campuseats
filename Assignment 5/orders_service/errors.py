from flask import jsonify


def problem(status, title, detail, type_=None):
    response = jsonify({'type': type_ or f"https://campuseats.example/problems/{title.lower().replace(' ', '-')}", 'title': title, 'status': status, 'detail': detail})
    response.status_code = status
    response.content_type = 'application/json'
    return response

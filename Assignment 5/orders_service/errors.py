from xml.etree.ElementTree import Element, SubElement, tostring
from flask import Response, jsonify


def problem(status: int, type_: str, title: str, detail: str, errors: list[dict[str, str]] | None = None, retry_after: int | None = None) -> Response:
    body: dict[str, object] = {
        'type': type_,
        'title': title,
        'status': status,
        'detail': detail,
    }
    if errors is not None:
        body['errors'] = errors
    response = jsonify(body)
    response.status_code = status
    response.content_type = 'application/problem+json; charset=utf-8'
    response.headers['Cache-Control'] = 'no-store'
    if retry_after is not None:
        response.headers['Retry-After'] = str(retry_after)
    return response


def _append_order_fields(node: Element, order_data: dict[str, object]) -> None:
    for key, value in order_data.items():
        if key == 'items' and isinstance(value, list):
            items_el = SubElement(node, 'items')
            for item in value:
                item_el = SubElement(items_el, 'item')
                for k, v in item.items():
                    SubElement(item_el, k).text = str(v)
        else:
            SubElement(node, key).text = str(value)


def xml_response(status: int, body: dict[str, object]) -> Response:
    if 'orderId' in body:
        root = Element('order')
        _append_order_fields(root, body)
    else:
        root = Element('orders')
        for key, value in body.items():
            if key == 'orders' and isinstance(value, list):
                for order_data in value:
                    order_el = SubElement(root, 'order')
                    _append_order_fields(order_el, order_data)
            else:
                SubElement(root, key).text = str(value)
    xml_bytes = '<?xml version="1.0" encoding="utf-8"?>\n' + tostring(root, encoding='unicode')
    return Response(xml_bytes, status=status, content_type='application/xml; charset=utf-8')

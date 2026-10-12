from flask import Response, jsonify


def problem(status, type_, title, detail, errors=None, retry_after=None):
    body = {'type': type_, 'title': title, 'status': status, 'detail': detail}
    if errors is not None: body['errors'] = errors
    response = jsonify(body)
    response.status_code = status
    response.content_type = 'application/problem+json; charset=utf-8'
    if retry_after is not None: response.headers['Retry-After'] = str(retry_after)
    return response


def xml_response(status, body):
    from xml.etree.ElementTree import Element, SubElement, tostring
    root = Element('order' if 'orderId' in body else 'orders')
    for key, value in body.items():
        if key == 'items':
            items = SubElement(root, 'items')
            for item in value:
                node = SubElement(items, 'item')
                for k, v in item.items(): SubElement(node, k).text = str(v)
        elif isinstance(value, list):
            for item in value:
                node = SubElement(root, 'order')
                for k, v in item.items(): SubElement(node, k).text = str(v)
        else: SubElement(root, key).text = str(value)
    return Response(tostring(root, encoding='unicode', xml_declaration=True), status=status, content_type='application/xml; charset=utf-8')

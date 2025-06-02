import requests


def get_bus_fare(start_stop_code, end_stop_code, route_id, ac=True) -> float:
    url = 'https://pre-prod-ondc-ticketing-api-delhi.transportstack.in/fetch_fare'
    body = {
        "start_stop_code": start_stop_code,
        "end_stop_code": end_stop_code,
        "route_id": route_id,
        "variant": "ac"
    }
    resp = requests.post(url, json=body).json()

    if resp['message'] == 'Success':
        return float(resp['data'].get('fare', 10))
    else:
        return 10

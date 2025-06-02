from flask import Flask, jsonify, request
import requests
from datetime import datetime, timedelta

CLIENT_ID = 'yyyH2lXd0mYCywkfS9bOPpMONUrZW2N1'
CLIENT_SECRET = 'Idiy1vXcJjKydmNt'

app = Flask(__name__)

DESTINATIONS = [
    ("FCO", "רומא"),
    ("CDG", "פריז"),
    ("LON", "לונדון"),
    ("BCN", "ברצלונה"),
    ("MAD", "מדריד"),
    ("VAR", "ורנה"),
    ("AMS", "אמסטרדם"),
]

def get_token():
    auth_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET
    }
    response = requests.post(auth_url, data=auth_data)

    try:
        token = response.json()['access_token']
        return token
    except KeyError:
        print("== ERROR getting token ==")
        print("Status Code:", response.status_code)
        print("Response:", response.text)
        return None


def get_cheapest_flight(origin, destination, departure_date, adults=1, max_results=10):
    token = get_token()
    search_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
    params = {
        'originLocationCode': origin,
        'destinationLocationCode': destination,
        'departureDate': departure_date,
        'adults': adults,
        'max': max_results
    }
    headers = {'Authorization': f'Bearer {token}'}
    resp = requests.get(search_url, headers=headers, params=params)

    offers = resp.json().get('data', [])
    best_flight = None
    best_price = float('inf')
    for offer in offers:
        try:
            seg = offer["itineraries"][0]["segments"][0]
            flight_number = seg["carrierCode"] + seg["flightNumber"]
            origin_code = seg["departure"]["iataCode"]
            dest_code = seg["arrival"]["iataCode"]
            price = float(offer["price"]["total"])
            airline = seg["carrierCode"]
            dep_time = seg["departure"]["at"]
            arr_time = seg["arrival"]["at"]
            if price < best_price:
                best_price = price
                best_flight = {
                    "destination": dest_code,
                    "destination_name": [n for code, n in DESTINATIONS if code == destination][0],
                    "flight": flight_number,
                    "airline": airline,
                    "price": price,
                    "dep_time": dep_time,
                    "arr_time": arr_time,
                    "origin": origin_code
                }
        except Exception:
            continue
    return best_flight


@app.route('/flights')
def api_flights():
    origin = request.args.get("origin", "TLV")
    date = request.args.get("date")
    if not date:
        date = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')

    adults = int(request.args.get("adults", 1))
    results = []
    for dest_code, dest_name in DESTINATIONS:
        flight = get_cheapest_flight(origin, dest_code, date, adults)
        if flight:
            results.append(flight)

    # 🟢 שליחה ל־n8n רק אחרי שהסתיימה הלולאה
    if results:
        webhook_url = "https://ronenv.app.n8n.cloud/webhook/7de5db6c-451c-4591-9ad0-c91ce4f9cf5d"
        try:
            res = requests.post(webhook_url, json=results)
            print("📡 נשלח ל־n8n! Status:", res.status_code)
        except Exception as e:
            print("❌ שגיאה בשליחה ל־n8n:", e)

    return jsonify(results)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)

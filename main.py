import streamlit as st
import requests
import urllib.parse
from datetime import datetime

# —— פרטי גישה לאמדאוס ——
CLIENT_ID = 'yyyH2lXd0mYCywkfS9bOPpMONUrZW2N1'
CLIENT_SECRET = 'Idiy1vXcJjKydmNt'

st.set_page_config(page_title="חיפוש טיסות", layout="wide")
st.title("✈️ חיפוש טיסות מתקדם")
st.header("סורק טיסות – בחר וסנן טיסות")

# —— עיצוב RTL וקלפים מותאמים למובייל ——
st.markdown("""
<style>
body { direction: rtl !important; }
[data-testid="stMarkdownContainer"] { direction: rtl; }
.flight-card {
    border: 2px solid #FFD700;
    border-radius: 20px;
    margin: 18px 0;
    padding: 22px 14px 10px 14px;
    background: linear-gradient(90deg,#26343e 60%,#2a3d4d 100%);
    color: #fff;
    box-shadow: 0 2px 10px #0002;
    font-size: 1.13em;
    line-height: 1.8;
    max-width: 600px;
    position: relative;
}
@media (max-width: 700px) {
  .flight-card {
    font-size: 1.25em;
    padding: 25px 7px 12px 7px;
    min-width: 0;
  }
}
.price-tag {
    font-size: 2em;
    color: #FFD700;
    float: left;
    margin-left: 15px;
    font-weight: bold;
}
.direct-label {
    color: #55FF66;
    font-weight: bold;
    margin-right: 7px;
    font-size: 1em;
}
.whatsapp-btn {
    display: inline-block;
    margin-top: 12px;
    background: #25d366;
    color: #fff !important;
    padding: 7px 18px;
    border-radius: 8px;
    text-decoration: none;
    font-weight: bold;
    font-size: 1.05em;
    transition: background 0.2s;
}
.whatsapp-btn:hover {
    background: #128c7e;
}
</style>
""",
            unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("קוד שדה תעופה יציאה (למשל TLV)", "TLV")
    departure_date = st.date_input("תאריך טיסה",
                                   datetime.today()).strftime('%Y-%m-%d')
    roundtrip = st.checkbox("טיסת הלוך-חזור? (Round trip)", value=False)
with col2:
    destination = st.text_input("קוד שדה תעופה יעד (למשל LON)", "LON")
    adults = st.number_input("מספר נוסעים", min_value=1, max_value=10, value=1)
    return_date = None
    if roundtrip:
        return_date = st.date_input("תאריך חזור",
                                    datetime.today()).strftime('%Y-%m-%d')


# פונקציה לשליפת טיסות
def get_flights(date, orig, dest, adults):
    search_url = 'https://test.api.amadeus.com/v2/shopping/flight-offers'
    params = {
        'originLocationCode': orig.upper(),
        'destinationLocationCode': dest.upper(),
        'departureDate': date,
        'adults': adults,
        'max': 30,
    }
    resp = requests.get(search_url,
                        headers=st.session_state['headers'],
                        params=params)
    return resp.json().get('data', [])


# פונקציה לכפתור וואטסאפ
def whatsapp_button(offer, idx, type_title="טיסה"):
    segs = offer['itineraries'][0]['segments']
    airline = segs[0]['carrierCode']
    dep_time = segs[0]['departure']['at'].replace("T", "  ")
    arr_time = segs[-1]['arrival']['at'].replace("T", "  ")
    price = offer['price']['total']
    stops = len(segs) - 1
    duration = offer['itineraries'][0]['duration'].replace("PT", "").lower()
    direct_label = 'ישירה' if stops == 0 else f'{stops} קונקשן'

    text = f"""✈️ {type_title} {idx} - {airline}
{direct_label}
יציאה: {dep_time}
נחיתה: {arr_time}
משך טיסה: {duration}
מחיר: €{price}
"""
    encoded = urllib.parse.quote(text)
    wa_url = f"https://wa.me/?text={encoded}"
    st.markdown(
        f'<a href="{wa_url}" target="_blank" class="whatsapp-btn">שלח ב־WhatsApp</a>',
        unsafe_allow_html=True)


# פונקציה להצגת קלפים
def show_flights_card(offers, title="טיסות נמצאו", type_title="טיסה"):
    if not offers:
        st.warning("לא נמצאו טיסות!")
        return

    st.subheader(title)
    for idx, offer in enumerate(offers, 1):
        segs = offer['itineraries'][0]['segments']
        airline = segs[0]['carrierCode']
        dep_time = segs[0]['departure']['at'].replace("T", "  ")
        arr_time = segs[-1]['arrival']['at'].replace("T", "  ")
        price = offer['price']['total']
        stops = len(segs) - 1
        duration = offer['itineraries'][0]['duration'].replace("PT",
                                                               "").lower()
        direct_label = 'ישירה' if stops == 0 else f'{stops} קונקשן'

        card_html = f"""
        <div class="flight-card">
            <div>
                <span class="price-tag">€{price}</span>
                <b>✈️ {type_title} {idx} - {airline}</b>
                <span class="direct-label">{direct_label}</span>
            </div>
            <div style="clear:both"></div>
            <div style="margin-top:14px;">
                <b>יציאה:</b> {dep_time}<br>
                <b>נחיתה:</b> {arr_time}<br>
                <b>משך טיסה:</b> {duration}
            </div>
        </div>
        """
        st.markdown(card_html, unsafe_allow_html=True)
        whatsapp_button(offer, idx, type_title)


# --- לוגיקה עיקרית: שמירה ב-session_state ---
if 'flight_offers' not in st.session_state:
    st.session_state['flight_offers'] = None
if 'flight_offers_return' not in st.session_state:
    st.session_state['flight_offers_return'] = None

if st.button("🔎 חפש טיסות"):
    with st.spinner("מחפש טיסות..."):
        # קבלת access_token פעם אחת
        auth_url = 'https://test.api.amadeus.com/v1/security/oauth2/token'
        auth_data = {
            'grant_type': 'client_credentials',
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }
        auth_response = requests.post(auth_url, data=auth_data)
        access_token = auth_response.json()['access_token']
        st.session_state['headers'] = {
            'Authorization': f'Bearer {access_token}'
        }

        # שמור תוצאות ב-session_state (רק אחרי חיפוש)
        st.session_state['flight_offers'] = get_flights(
            departure_date, origin, destination, adults)
        st.session_state['flight_offers_return'] = get_flights(
            return_date, destination, origin,
            adults) if (roundtrip and return_date) else None

if st.session_state['flight_offers']:
    flight_offers = st.session_state['flight_offers']
    flight_offers_return = st.session_state['flight_offers_return']

    # מחשבים ערכי סינון דינמיים
    all_prices = [float(offer['price']['total']) for offer in flight_offers]
    min_price = int(min(all_prices))
    max_price = int(max(all_prices))
    price_range = (min_price,
                   max_price) if min_price != max_price else (min_price,
                                                              max_price + 1)

    airlines = sorted(
        list({
            offer['itineraries'][0]['segments'][0]['carrierCode']
            for offer in flight_offers
        }))
    hours = [
        int(offer['itineraries'][0]['segments'][0]['departure']['at'][11:13])
        for offer in flight_offers
    ]
    min_hour, max_hour = min(hours), max(hours)
    st.markdown("#### אפשרויות סינון")

    price_selected = st.slider("טווח מחיר (€):", min_price, max_price,
                               (min_price, max_price))
    selected_airline = st.selectbox("סנן לפי חברת תעופה:", ["הכל"] + airlines,
                                    key="outbound_airline")
    selected_hours = st.slider("שעת יציאה (טווח):",
                               min_hour,
                               max_hour, (min_hour, max_hour),
                               step=1,
                               format="%02d")
    connection_type = st.radio("סוג טיסה:", ["הכל", "ישיר בלבד", "עם קונקשן"])

    def filter_flights(offers):
        filtered = []
        for offer in offers:
            segs = offer['itineraries'][0]['segments']
            airline = segs[0]['carrierCode']
            hour = int(segs[0]['departure']['at'][11:13])
            price = float(offer['price']['total'])
            is_direct = len(segs) == 1
            if price < price_selected[0] or price > price_selected[1]:
                continue
            if selected_airline != "הכל" and airline != selected_airline:
                continue
            if not (selected_hours[0] <= hour <= selected_hours[1]):
                continue
            if connection_type == "ישיר בלבד" and not is_direct:
                continue
            if connection_type == "עם קונקשן" and is_direct:
                continue
            filtered.append(offer)
        return filtered

    filtered_offers = filter_flights(flight_offers)
    st.success(f"נמצאו {len(filtered_offers)} טיסות הלוך!")
    show_flights_card(filtered_offers,
                      title="✈️ טיסות הלוך",
                      type_title="טיסה הלוך")

    # --- טיסות חזור ---
    if flight_offers_return:
        filtered_return = filter_flights(flight_offers_return)
        st.success(f"נמצאו {len(filtered_return)} טיסות חזור!")
        show_flights_card(filtered_return,
                          title="✈️ טיסות חזור",
                          type_title="טיסת חזור")

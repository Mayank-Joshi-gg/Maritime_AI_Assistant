import streamlit as st
import requests
import mysql.connector
from openai import OpenAI
import math
import pyttsx3

# -----------------------
# 🔑 Secrets & API Keys
# -----------------------
OPENAI_KEY = st.secrets["OPENAI_KEY"]
WEATHER_KEY = st.secrets["WEATHER_KEY"]

# OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# -----------------------
# Streamlit Page Config
# -----------------------
st.set_page_config(page_title="Maritime Assistant", page_icon="⚓", layout="wide")

# ----------------
# Avatar Display
# ----------------
st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
avatar_url = "https://cdn-icons-png.flaticon.com/512/4140/4140044.png"  # Example nautical captain avatar
st.image(avatar_url, width=150)
st.markdown("</div>", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center; color: navy;'>⚓ Maritime Virtual Assistant</h1>", unsafe_allow_html=True)
st.markdown("---")

# -----------------------
# MySQL Connection Functions
# -----------------------
def get_connection():
    return mysql.connector.connect( 
        host=st.secrets["mysql"]["host"],
        user=st.secrets["mysql"]["user"],
        password=st.secrets["mysql"]["password"],
        database=st.secrets["mysql"]["database"]
    )

def save_vessel_to_db(vessel):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO vessels (imo, name, type, flag, year_built, tonnage)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            name=VALUES(name), type=VALUES(type), flag=VALUES(flag),
            year_built=VALUES(year_built), tonnage=VALUES(tonnage)
    """, (
        vessel["imo"], vessel["name"], vessel["type"],
        vessel["flag"], vessel["year_built"], vessel["tonnage"]
    ))
    conn.commit()
    cursor.close()
    conn.close()

def get_vessel_from_db(imo):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM vessels WHERE imo = %s", (imo,))
    vessel = cursor.fetchone()
    cursor.close()
    conn.close()
    return vessel

# -----------------------
# Weather Function
# -----------------------
def get_weather(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={WEATHER_KEY}"
    geo_data = requests.get(geo_url).json()
    if not geo_data:
        return "⚠️ City not found."
    lat, lon = geo_data[0]["lat"], geo_data[0]["lon"]

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
    weather_data = requests.get(weather_url).json()

    try:
        description = weather_data["weather"][0]["description"].capitalize()
        temp = weather_data["main"]["temp"]
        wind = weather_data["wind"]["speed"]
        return (
            f"📍 Location: {city_name}\n"
            f"🌤 Weather: {description}\n"
            f"🌡 Temperature: {temp} °C\n"
            f"💨 Wind Speed: {wind} m/s"
        )
    except KeyError:
        return "⚠️ Unable to fetch weather data."

# -----------------------
# GPT Maritime Questions
# -----------------------
def ask_maritime_question(question):
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful maritime assistant."},
                {"role": "user", "content": question}
            ]
        )
        return response.choices[0].message.content
    except Exception:
        return "⚠️ AI response failed."

# -----------------------
# Voyage Estimation
# -----------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 3440.065  # Nautical miles
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

def estimate_voyage_time(distance_nm, speed_knots):
    hours = distance_nm / speed_knots
    days = hours / 24
    return hours, days

def get_port_coordinates(port_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={port_name}&limit=1&appid={WEATHER_KEY}"
    geo_data = requests.get(geo_url).json()
    if geo_data:
        return geo_data[0]["lat"], geo_data[0]["lon"]
    return None, None

# -----------------------
# Streamlit UI
# -----------------------
mode = st.radio("Choose an action:", [
    "Ask a Maritime Question",
    "Check Sea Weather",
    "Get Vessel Info (DB Only)",
    "Estimate Voyage"
])

st.markdown("---")

# --- Maritime Q&A
if mode == "Ask a Maritime Question":
    st.subheader("📝 Ask a Maritime Question")
    user_question = st.text_input("Type your maritime question here:")
    if st.button("Ask"):
        if user_question.strip():
            answer = ask_maritime_question(user_question)
            st.info(answer)
        else:
            st.warning("Please enter a question.")

# --- Weather Check
elif mode == "Check Sea Weather":
    st.subheader("🌦 Check Sea Weather")
    city_input = st.text_input("Enter a port or city name:")
    if st.button("Get Weather"):
        if city_input.strip():
            weather_info = get_weather(city_input)
            st.success(weather_info)
        else:
            st.warning("Please enter a city name.")

# --- Vessel Info
elif mode == "Get Vessel Info (DB Only)":
    st.subheader("⚓ Vessel Information")
    imo_input = st.text_input("Enter Vessel IMO number:")
    if st.button("Search Vessel"):
        if imo_input.strip():
            vessel = get_vessel_from_db(imo_input)
            if vessel:
                st.json(vessel)
            else:
                st.error("⚠️ Vessel not found in database.")
        else:
            st.warning("Please enter a valid IMO number.")

# --- Voyage Estimation
elif mode == "Estimate Voyage":
    st.subheader("🧭 Voyage Estimation")
    col1, col2 = st.columns(2)
    with col1:
        source_port = st.text_input("Source Port")
    with col2:
        dest_port = st.text_input("Destination Port")
    avg_speed = st.number_input("Average Speed (knots)", min_value=1.0, value=15.0)

    if st.button("Estimate ETA"):
        if source_port.strip() and dest_port.strip():
            src_lat, src_lon = get_port_coordinates(source_port)
            dest_lat, dest_lon = get_port_coordinates(dest_port)

            if None in (src_lat, src_lon, dest_lat, dest_lon):
                st.error("⚠️ Could not find coordinates for one or both ports.")
            else:
                distance = haversine(src_lat, src_lon, dest_lat, dest_lon)
                hours, days = estimate_voyage_time(distance, avg_speed)
                st.success(
                    f"📍 From: {source_port} → To: {dest_port}\n"
                    f"🧭 Distance: {distance:.2f} Nautical Miles\n"
                    f"⏱ Estimated Time: {hours:.2f} hours (~{days:.2f} days) at {avg_speed} knots"
                )
        else:
            st.warning("Please enter both source and destination ports.")
engine=pyttsx3.init()
engine.say('''Welcome to maritime assistant
              This is a virtual assistant for maritime queries
              You can ask about weather, vessel info, voyage estimation and general maritime questions
           ''')
engine.runAndWait()

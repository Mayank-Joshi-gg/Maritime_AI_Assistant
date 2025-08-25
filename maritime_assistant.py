import streamlit as st
import requests
from openai import OpenAI

# ✅ Get keys securely from Streamlit Cloud secrets
OPENAI_KEY = st.secrets["OPENAI_KEY"]
WEATHER_KEY = st.secrets["WEATHER_KEY"]

# Set up OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# Streamlit page setup
st.set_page_config(page_title="Maritime Assistant", page_icon="⚓")
st.title("⚓ Maritime Virtual Assistant")
st.write("Welcome aboard! Ask maritime questions or check live sea weather.")

# 🌦 Function to get weather data
def get_weather(city_name):
    geo_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city_name}&limit=1&appid={WEATHER_KEY}"
    geo_data = requests.get(geo_url).json()

    if not geo_data:
        return "⚠️ City not found. Please check the spelling."

    lat = geo_data[0]["lat"]
    lon = geo_data[0]["lon"]

    weather_url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={WEATHER_KEY}&units=metric"
    weather_data = requests.get(weather_url).json()

    try:
        description = weather_data["weather"][0]["description"].capitalize()
        temperature = weather_data["main"]["temp"]
        wind_speed = weather_data["wind"]["speed"]

        return (
            f"📍 Location: {city_name}\n"
            f"🌤 Weather: {description}\n"
            f"🌡 Temperature: {temperature} °C\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )
    except KeyError:
        return "⚠️ Unable to fetch weather data. Try again later."

# 🧭 Function to ask maritime questions using GPT
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
        return "⚠️ AI response failed. Please check your API key or quota."

# 🖥️ User Interface
mode = st.radio("Choose what you want to do:", ["Ask a Maritime Question", "Check Sea Weather"])

if mode == "Ask a Maritime Question":
    user_question = st.text_input("Type your maritime question:")
    if st.button("Ask"):
        if user_question.strip():
            answer = ask_maritime_question(user_question)
            st.success(answer)
        else:
            st.warning("Please enter a question.")

elif mode == "Check Sea Weather":
    city_input = st.text_input("Enter a port or city name:")
    if st.button("Get Weather"):
        if city_input.strip():
            weather_info = get_weather(city_input)
            st.info(weather_info)
        else:
            st.warning("Please enter a city name.")

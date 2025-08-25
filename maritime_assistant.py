import streamlit as st
import requests

# ------------------ Load Secrets ------------------ #
HF_API_KEY = st.secrets["HF_API_KEY"]     # Hugging Face API token
WEATHER_KEY = st.secrets["WEATHER_KEY"]  # OpenWeather API key

# ------------------ Hugging Face Q&A ------------------ #
HF_MODEL = "distilgpt2"  # Small, stable, free-tier model

def ask_maritime_question(question):
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": question}

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload,
            timeout=60  # Wait up to 60 seconds for the model to load
        )

        # Check HTTP response
        if response.status_code != 200:
            return f"⚠️ HuggingFace API returned {response.status_code}: {response.text}"

        # Parse JSON response
        try:
            data = response.json()
        except Exception:
            return "⚠️ HuggingFace returned invalid response. Try again."

        # Handle empty or unexpected responses
        if not data:
            return "⚠️ HuggingFace returned empty response. Try again."

        # Extract generated text
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        elif isinstance(data, dict) and "generated_text" in data:
            return data["generated_text"]
        elif isinstance(data, dict) and "error" in data:
            return f"⚠️ HuggingFace error: {data['error']}"
        else:
            return str(data)

    except requests.Timeout:
        return "⚠️ Request timed out. Try again in a few seconds."
    except Exception as e:
        return f"⚠️ Unexpected error: {str(e)}"


# ------------------ Weather Feature ------------------ #
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"⚠️ Error: {data.get('message', 'City not found')}"

        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"].capitalize()
        wind_speed = data["wind"]["speed"]

        return (
            f"📍 Location: {city}\n"
            f"🌡 Temperature: {temp} °C\n"
            f"🌤 Condition: {condition}\n"
            f"💨 Wind Speed: {wind_speed} m/s"
        )

    except Exception as e:
        return f"⚠️ Weather error: {str(e)}"


# ------------------ Streamlit UI ------------------ #
st.set_page_config(page_title="Maritime AI Assistant", page_icon="⚓")
st.title("⚓ Maritime AI Assistant (Free Hugging Face Version)")

menu = st.sidebar.radio("Choose Option", ["Maritime Q&A", "Weather Info"])

if menu == "Maritime Q&A":
    st.subheader("Ask a Maritime Question")
    question = st.text_input("Enter your question here:")
    if st.button("Ask"):
        if question.strip():
            with st.spinner("Thinking..."):
                answer = ask_maritime_question(question)
            st.success("Answer:")
            st.write(answer)
        else:
            st.warning("Please enter a question.")

elif menu == "Weather Info":
    st.subheader("Check Weather at Port/City")
    city = st.text_input("Enter city name:")
    if st.button("Get Weather"):
        if city.strip():
            with st.spinner("Fetching weather..."):
                weather = get_weather(city)
            st.success("Weather:")
            st.write(weather)
        else:
            st.warning("Please enter a city name.")

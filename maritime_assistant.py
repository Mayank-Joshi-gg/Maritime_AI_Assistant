import streamlit as st
import requests

# Load keys from Streamlit secrets
HF_API_KEY = st.secrets["HF_API_KEY"]   # Hugging Face token
WEATHER_KEY = st.secrets["WEATHER_KEY"] # OpenWeather API key

# Hugging Face model (you can try others like "gpt2", "distilgpt2", "google/flan-t5-small")
HF_MODEL = "google/flan-t5-small"


# ------------------ Hugging Face Q&A ------------------ #
def ask_maritime_question(question):
    try:
        headers = {"Authorization": f"Bearer {HF_API_KEY}"}
        payload = {"inputs": question}

        response = requests.post(
            f"https://api-inference.huggingface.co/models/{HF_MODEL}",
            headers=headers,
            json=payload
        )

        data = response.json()

        # Handle possible return formats
        if isinstance(data, list) and "generated_text" in data[0]:
            return data[0]["generated_text"]
        elif "generated_text" in data:
            return data["generated_text"]
        elif "error" in data:
            return f"⚠️ HuggingFace error: {data['error']}"
        else:
            return str(data)
    except Exception as e:
        return f"⚠️ Error: {str(e)}"


# ------------------ Weather Info ------------------ #
def get_weather(city):
    try:
        url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}&units=metric"
        response = requests.get(url)
        data = response.json()

        if data.get("cod") != 200:
            return f"⚠️ Error: {data.get('message', 'City not found')}"
        
        temp = data["main"]["temp"]
        condition = data["weather"][0]["description"]
        return f"🌡️ {temp}°C, {condition}"
    except Exception as e:
        return f"⚠️ Weather error: {str(e)}"


# ------------------ Streamlit UI ------------------ #
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


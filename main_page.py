import streamlit as st
import pandas as pd
import openai
import requests
import random
import json
import tempfile
from dotenv import load_dotenv
from openai import OpenAI
from fpdf import FPDF
from streamlit_folium import st_folium
import folium

# Load environment variables
load_dotenv()

# Setup OpenAI and Google Maps
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLEMAPS_API_KEY = st.secrets["GOOGLEMAPS_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# Page config
st.set_page_config(page_title="AquaED", page_icon="💧", layout="wide")

# AquaED Logo + Navbar
col1, col2 = st.columns([1, 8])
with col1:
    st.image("aquaed_logo.png", width=100)
with col2:
    st.markdown("<h1 style='color:#003049; padding-top: 20px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)

st.markdown("---")

# Tabs (no page reloads anymore!)
tabs = st.tabs(["🏠 Home", "📚 AquaEducator", "💧 AquaEdvisor", "🗺️ AquaMap"])

# -------------------------------------------------------------------------------------------------
# 🏠 Home
with tabs[0]:
    st.header("🏠 Welcome to AquaED!")
    st.write("This is your main homepage. Use the tabs above to explore water quality education, filter recommendations, and location-based resources.")

# -------------------------------------------------------------------------------------------------
# 📚 AquaEducator
with tabs[1]:
    st.header("📚 AquaEducator")

    option = st.selectbox("Select language", ("English", "Spanish", "Vietnamese", "Mandarin", "Korean"))

    tab1, tab2, tab3 = st.tabs(["Water Fun Facts", "Water Quality FAQ", "Water Quality Quiz"])

    # --- Fun Fact
    with tab1:
        st.subheader("🌊 Water Fun Fact 🌊")
        if "fun_fact" not in st.session_state:
            st.session_state.fun_fact = ""
            st.session_state.fun_fact_audio = None

        def get_completion(prompt, model="gpt-3.5-turbo"):
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert on water quality."},
                    {"role": "user", "content": prompt},
                ]
            )
            return completion.choices[0].message.content

        def speak_text(text, voice="nova"):
            try:
                response = openai.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=text
                )
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
                    tmp.write(response.read())
                    return tmp.name
            except Exception:
                st.warning("TTS failed.")
                return None

        with st.form(key="chat"):
            prompt = st.text_input("Want a local fact? Enter your city:")
            submitted = st.form_submit_button("🔍 Generate a Fun Fact")

        if submitted and prompt:
            fact_prompt = f"Give me one short, interesting fun fact about {prompt} water quality, translate into {option} language. Start with 'Did you know?'"
            description = get_completion(fact_prompt)
            st.session_state.fun_fact = description
            st.session_state.fun_fact_audio = speak_text(description)

        if st.session_state.fun_fact:
            st.write(st.session_state.fun_fact)
            if st.button("🔈 Play fun fact"):
                if st.session_state.fun_fact_audio:
                    st.audio(st.session_state.fun_fact_audio)
                else:
                    st.warning("Audio not available.")

    # --- FAQ
    with tab2:
        st.subheader("Water Quality FAQs")
        questions = [
            "What is pH in water?",
            "How can I measure water quality at home?",
            "Why is chlorine added to water?",
            "What are nitrates and why are they bad?",
            "How is my water cleaned?",
            "What are safe levels of lead in water?",
            "Where are the water treatment plants near me?"
        ]

        selected_question = st.selectbox("Select a question:", questions)

        if selected_question:
            with st.spinner("Asking GPT..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "You are a water quality expert in Santa Clara County."},
                            {"role": "user", "content": f"Answer: {selected_question}. Translate into {option} language."}
                        ],
                        temperature=0.7,
                        max_tokens=300
                    )
                    answer = response.choices[0].message.content
                    st.markdown(f"**Answer:** {answer}")
                except Exception as e:
                    st.error(f"Something went wrong: {str(e)}")

        st.markdown("[Learn more from Valley Water](https://www.valleywater.org/your-water/water-quality)")

    # --- Quiz
    with tab3:
        st.subheader("💧 Water Quality Quiz")
        if "quiz_questions" not in st.session_state:
            with open("questions.json", "r") as f:
                all_questions = json.load(f)
            random.shuffle(all_questions)
            st.session_state.quiz_questions = all_questions[:3]
            st.session_state.quiz_answers = [None] * 3
            st.session_state.quiz_submitted = False

        for idx, q in enumerate(st.session_state.quiz_questions):
            st.subheader(f"Q{idx + 1}: {q['question']}")
            st.session_state.quiz_answers[idx] = st.radio(
                "Your answer:",
                q["options"],
                key=f"quiz_{idx}"
            )

        if st.button("✅ Submit Quiz"):
            st.session_state.quiz_submitted = True
            score = sum(1 for idx, q in enumerate(st.session_state.quiz_questions) if st.session_state.quiz_answers[idx] == q["answer"])
            st.success(f"Your score: {score} / 3")

        if st.session_state.quiz_submitted and st.button("🔁 Restart Quiz"):
            for key in list(st.session_state.keys()):
                if key.startswith("quiz_") or key in ["quiz_questions", "quiz_answers", "quiz_submitted"]:
                    del st.session_state[key]
            st.rerun()

# -------------------------------------------------------------------------------------------------
# 💧 AquaEdvisor
with tabs[2]:
    st.header("💧 AquaEdvisor")
    product_df = pd.read_csv("water_filter_recommendations_detailed.csv")

    budget_mapping = {
        "Under $50": 50,
        "$50–$100": 100,
        "$100–$200": 200,
        "Over $200": float('inf')
    }

    language = st.selectbox("🌐 Select Language:", ["English", "Spanish", "Vietnamese", "Mandarin", "Korean"])

    zip_code = st.text_input("Enter your ZIP code:")
    issues = st.text_area("Describe any water issues you've noticed:")
    budget = st.selectbox("Filter budget?", list(budget_mapping.keys()))
    is_parent = st.checkbox("Young children at home")
    is_renter = st.checkbox("I rent my home")
    is_senior = st.checkbox("I'm a senior (65+)")
    is_eco_focused = st.checkbox("Eco-friendly preference")

    if st.button("Generate Recommendations"):
        traits = []
        if is_parent: traits.append("parent")
        if is_renter: traits.append("renter")
        if is_senior: traits.append("senior")
        if is_eco_focused: traits.append("eco-focused")
        user_traits = ", ".join(traits) if traits else "general user"

        prompt = f"User in ZIP {zip_code} has water issues: {issues}. Budget: {budget}. Traits: {user_traits}. Generate recommendations and translate into {language}."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful water quality expert."}, {"role": "user", "content": prompt}]
            )
            st.markdown(response.choices[0].message.content)

            st.subheader("🛍️ Filter Options")
            budget_limit = budget_mapping[budget]
            filtered_products = product_df[product_df["Price_Value"] <= budget_limit]

            for _, row in filtered_products.iterrows():
                st.markdown(f"### [{row['Product Name']}]({row['Link']})")
                st.image(row['Image_URL'], width=500)
                st.markdown(f"Type: {row['Type']} | Price: {row['Price']}")
                st.markdown("---")
        except Exception as e:
            st.error(f"Error generating recommendations: {e}")

# -------------------------------------------------------------------------------------------------
# 🗺️ AquaMap
with tabs[3]:
    st.header("🗺️ AquaMap")

    df = pd.read_csv("bayareawater.csv")

    def get_zip(lat, lon):
        url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={lat},{lon}&key={GOOGLEMAPS_API_KEY}"
        response = requests.get(url)
        data = response.json()
        if data["status"] == "OK":
            for component in data["results"][0]["address_components"]:
                if "postal_code" in component["types"]:
                    return component["short_name"]
        return None

    map = folium.Map(location=[37.6110, -122.2050], zoom_start=10)
    map.add_child(folium.LatLngPopup())
    map_data = st_folium(map, width=700, height=500)

    if map_data and map_data["last_clicked"]:
        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]

    if st.button("Submit Location"):
        user_zip = get_zip(latitude, longitude)
        if user_zip:
            match = df[df["ZIP Code"] == int(user_zip)]
            if match.empty:
                st.write("No water quality data found.")
            else:
                entry = match.iloc[0]
                st.write(f"{entry['City']} (ZIP {user_zip}): Water quality score {entry['Water Quality Score']}, Contaminants: {entry['Common Contaminants']}")

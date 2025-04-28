import streamlit as st
import pandas as pd
import openai
import requests
import random
import json
import tempfile
from dotenv import load_dotenv
from fpdf import FPDF
from openai import OpenAI
from streamlit_folium import st_folium
import folium

# --- Load environment variables ---
load_dotenv()

OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLEMAPS_API_KEY = st.secrets["GOOGLEMAPS_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# --- Page config ---
st.set_page_config(page_title="AquaED", page_icon="💧", layout="wide")

# --- Centered Logo and Title using st.image() ---
st.markdown("<div style='text-align: center; margin-top: -40px;'>", unsafe_allow_html=True)
st.image("aquaed_logo.png", width=500)
st.markdown("<h1 style='color:#003049; font-size:48px; margin-top: 10px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)
st.markdown("</div>", unsafe_allow_html=True)

# --- Optional thin separator line ---
st.markdown("<hr style='margin-top: 10px; margin-bottom: 10px; border: 1px solid #0077B6;'>", unsafe_allow_html=True)

# --- Smooth fade-in animation ---
st.markdown("""
    <style>
    /* Smooth fade animation */
    div[data-testid="stVerticalBlock"] > div {
        animation: fadeEffect 0.7s;
    }
    @keyframes fadeEffect {
        from {opacity: 0;}
        to {opacity: 1;}
    }

    /* --- Make Tabs Fonts Larger --- */
    button[data-baseweb="tab"] {
        font-size: 30px !important; /* <-- adjust the number bigger or smaller */
        font-weight: bold;
        padding: 12px 20px;
    }
    
    /* Hide fullscreen expand button on images */
    button[title="View fullscreen"] {
        display: none;
    }

    /* Hide the anchor link icon next to headings */
    h1:hover a, h2:hover a, h3:hover a {
        display: none;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("---")

# --- Main Tabs ---
main_tabs = st.tabs(["🏠 Home", "📚 AquaEducator", "💧 AquaEdvisor", "🗺️ AquaMap"])

# ===============================
# 🏠 Home
with main_tabs[0]:
    st.header("🏠 Welcome to AquaED!")
    st.write("Explore water quality education, get personalized filter advice, and discover your local water conditions!")

# ===============================
# 📚 AquaEducator
with main_tabs[1]:
    st.header("📚 AquaEducator")

    language_option = st.selectbox(
        "🌐 Select Language:", 
        ("English", "Spanish", "Vietnamese", "Mandarin", "Korean"), 
        key="educator_language"
    )
    edu_tabs = st.tabs(["Water Fun Facts", "Water Quality FAQ", "Water Quality Quiz"])

    # --- Water Fun Facts ---
    with edu_tabs[0]:
        st.subheader("🌊 Water Fun Fact")
        if "fun_fact" not in st.session_state:
            st.session_state.fun_fact = ""
            st.session_state.fun_fact_audio = None

        def get_completion(prompt, model="gpt-3.5-turbo"):
            completion = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are an expert on water quality."},
                    {"role": "user", "content": prompt}
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

        with st.form("fun_fact_form"):
            city_prompt = st.text_input("Enter your city for a local fun fact:")
            submitted = st.form_submit_button("🔍 Generate Fun Fact")

        if submitted and city_prompt:
            prompt = f"Give a short, interesting water fun fact about {city_prompt}. Translate it into {language_option}. Start with 'Did you know?'"
            fact = get_completion(prompt)
            st.session_state.fun_fact = fact
            st.session_state.fun_fact_audio = speak_text(fact)

        if st.session_state.fun_fact:
            st.write(st.session_state.fun_fact)
            if st.button("🔈 Play Fun Fact"):
                if st.session_state.fun_fact_audio:
                    st.audio(st.session_state.fun_fact_audio)
                else:
                    st.warning("Audio not available.")

    # --- Water Quality FAQ ---
    with edu_tabs[1]:
        st.subheader("Water Quality FAQ")

        questions = [
            "What is pH in water?",
            "How can I measure water quality at home?",
            "Why is chlorine added to water?",
            "What are nitrates and why are they bad?",
            "How is my water cleaned?",
            "What are safe levels of lead in water?",
            "Where are the water treatment plants near me?"
        ]

        faq_question = st.selectbox("Select a FAQ question:", questions)

        if faq_question:
            with st.spinner("Fetching answer..."):
                try:
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Expert in Santa Clara County water quality."},
                            {"role": "user", "content": f"Answer '{faq_question}' and translate to {language_option}."}
                        ]
                    )
                    answer = response.choices[0].message.content
                    st.markdown(f"**Answer:** {answer}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

    # --- Water Quality Quiz ---
    with edu_tabs[2]:
        st.subheader("💧 Water Quality Quiz")
        if "quiz_questions" not in st.session_state:
            with open("questions.json", "r") as f:
                quiz_data = json.load(f)
            random.shuffle(quiz_data)
            st.session_state.quiz_questions = quiz_data[:3]
            st.session_state.quiz_answers = [None]*3
            st.session_state.quiz_submitted = False

        for idx, q in enumerate(st.session_state.quiz_questions):
            st.subheader(f"Q{idx+1}: {q['question']}")
            st.session_state.quiz_answers[idx] = st.radio(
                "Select your answer:",
                q["options"],
                key=f"quiz_{idx}"
            )

        if st.button("✅ Submit Quiz"):
            st.session_state.quiz_submitted = True
            score = sum(
                1 for idx, q in enumerate(st.session_state.quiz_questions)
                if st.session_state.quiz_answers[idx] == q["answer"]
            )
            st.success(f"🎯 Your Score: {score} / 3")

        if st.session_state.quiz_submitted and st.button("🔁 Restart Quiz"):
            for key in list(st.session_state.keys()):
                if key.startswith("quiz_") or key in ["quiz_questions", "quiz_answers", "quiz_submitted"]:
                    del st.session_state[key]
            st.rerun()
# ===============================
# 💧 AquaEdvisor
with main_tabs[2]:
    st.header("💧 AquaEdvisor")

    product_df = pd.read_csv("water_filter_recommendations_detailed.csv")

    budget_mapping = {
        "Under $50": 50,
        "$50–$100": 100,
        "$100–$200": 200,
        "Over $200": float('inf')
    }

    advisor_language = st.selectbox(
        "🌐 Select Language:", 
        ["English", "Spanish", "Vietnamese", "Mandarin", "Korean"], 
        key="advisor_language"
    )

    zip_code = st.text_input("Enter your ZIP code:")
    issues = st.text_area("Describe any water issues you've noticed:")
    budget = st.selectbox("Select your budget:", list(budget_mapping.keys()))

    is_parent = st.checkbox("Young children at home")
    is_renter = st.checkbox("I rent my home")
    is_senior = st.checkbox("I'm a senior (65+)")
    is_eco_focused = st.checkbox("Eco-friendly preference")

    recommendations_text = ""
    translated_products = []

    if st.button("Generate Recommendations"):
        with st.spinner("Analyzing your water profile..."):
            traits = []
            if is_parent: traits.append("parent with young children")
            if is_renter: traits.append("renter")
            if is_senior: traits.append("senior citizen")
            if is_eco_focused: traits.append("eco-conscious")
            user_traits = ", ".join(traits) if traits else "general user"

            prompt = f"""
            You are a helpful assistant. The user lives in ZIP code {zip_code}.
            Water issues: {issues}.
            Budget: {budget}.
            Traits: {user_traits}.
            Provide a brief water quality concern summary and filter system recommendations.
            Translate into {advisor_language}.
            """

            try:
                response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a water quality expert."},
                        {"role": "user", "content": prompt}
                    ]
                )
                recommendations_text = response.choices[0].message.content
                st.success("Here are your personalized recommendations:")
                st.markdown(recommendations_text)

                st.subheader("🛍️ Featured Water Filters")

                budget_limit = budget_mapping[budget]
                filtered_products = product_df[product_df["Price_Value"] <= budget_limit]

                for _, row in filtered_products.iterrows():
                    st.markdown(f"### [{row['Product Name']}]({row['Link']})")
                    st.image(row['Image_URL'], width=500)
                    st.markdown(f"**Type:** {row['Type']}  |  **Price:** {row['Price']}")
                    st.markdown(f"**Best For:** {row['Best For']}")
                    st.markdown(f"**Pros:** {row['Pros']}")
                    st.markdown(f"**Cons:** {row['Cons']}")
                    st.markdown("---")

                product_text = "\n\n".join([
                    f"Name: {row['Product Name']}\nDescription: {row['Description']}\nPrice: {row['Price']}\nPros: {row['Pros']}\nCons: {row['Cons']}\nLink: {row['Link']}"
                    for _, row in filtered_products.iterrows()
                ])
                translation_prompt = f"Translate this product information into {advisor_language}:\n\n{product_text}"

                translation_response = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a professional translator."},
                        {"role": "user", "content": translation_prompt}
                    ]
                )
                translated_text = translation_response.choices[0].message.content
                translated_products = translated_text.split("\n\n")

            except Exception as e:
                st.error(f"Something went wrong: {e}")

    # --- Download PDF
    if recommendations_text and translated_products and st.button("📄 Download Report as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.multi_cell(0, 10, f"Water Quality Recommendations ({advisor_language})\n")
        pdf.multi_cell(0, 10, recommendations_text)

        for product_text in translated_products:
            pdf.ln(5)
            pdf.set_font("Arial", '', 12)
            pdf.multi_cell(0, 10, product_text)

        pdf.output("Water_Quality_Report.pdf")
        with open("Water_Quality_Report.pdf", "rb") as f:
            st.download_button("Download PDF", f, file_name="Water_Quality_Report.pdf")

# ===============================
# 🗺️ AquaMap
with main_tabs[3]:
    st.header("📍 AquaMap: A Location-based Water Quality Tool")

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

    def get_completion(prompt, model="gpt-3.5-turbo"):
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Reply with a list of four issues regarding water purification for the user's given city correlating with their zip code response. You must mention the name of the city. Each entry should be no more than 4 sentences long. Please add 'Continue exploring the app to see what you can do to help your community' at the end."},
                {"role": "user", "content": prompt},
            ]
        )
        return completion.choices[0].message.content

    def print_quality_info(zip_code):
        match = df[df["ZIP Code"] == zip_code]
        if match.empty:
            st.write("There is no water quality data found for this location.")
        else:
            entry = match.iloc[0]
            metro = entry["City"]
            score = entry["Water Quality Score"]
            contaminants = entry["Common Contaminants"]
            epa_status = "does" if entry["Meets EPA Standards"] == "Yes" else "does not"
            st.write(f"{metro} (ZIP code {zip_code}) has a water quality score of {score}, which {epa_status} meet EPA standards. Some common contaminants in {metro}'s water include: {contaminants}.")

    st.markdown("""
    Please select your location on the map and click "Submit Location" to learn more about water quality in your city. 
    For cities selected within the San Francisco Bay Area, additional information will be provided about water quality scores and common contaminants.
    """)

    map = folium.Map(location=[37.6110, -122.2050], zoom_start=10)
    map.add_child(folium.LatLngPopup())
    map_data = st_folium(map, width=700, height=500)

    if map_data and map_data.get("last_clicked"):
        latitude = map_data["last_clicked"]["lat"]
        longitude = map_data["last_clicked"]["lng"]

    if st.button("Submit Location"):
        if 'latitude' in locals() and 'longitude' in locals():
            user_zip = get_zip(latitude, longitude)
            if user_zip:
                print_quality_info(int(user_zip))
                st.write(get_completion(user_zip))
            else:
                st.error("Could not determine ZIP code from selected location.")
        else:
            st.error("Please click a location on the map first.")

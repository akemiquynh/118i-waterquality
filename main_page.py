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

@st.cache_data
def get_random_water_image():
    water_images = [
        "https://i.imgur.com/sfixLBQ.png",  # pouring water
        "https://i.imgur.com/iQEoOxk.png",  # washing fruits
        "https://i.imgur.com/EFO5i7u.png",  # faucet
        "https://i.imgur.com/cQ17Ktm.png",  # flower on water
        "https://i.imgur.com/JwXE4Iw.png"   # child drinking water
    ]
    return random.choice(water_images)

# --- Page config ---
st.set_page_config(page_title="AquaED", page_icon="💧", layout="wide")

# --- Perfectly Centered Logo, Title, and Subtitle (using pure HTML) ---
st.markdown("""
<div style="display: flex; flex-direction: column; align-items: center; justify-content: center; margin-top: -40px;">
    <img src="https://i.imgur.com/KpJbbvV.png" style="width: 500px; height: auto; margin-bottom: -10px;">
    <h1 style="color:#003049; font-size:48px; margin-top: 0px;">Water Quality Made Simple</h1>
    <h3 style="color:#0077B6; font-size:20px; font-weight: normal; margin-top: 5px;">Explore, Learn, and Protect Your Water</h3>
</div>
<hr style="margin-top: 10px; margin-bottom: 10px; border: 0.5px solid #0077B6;">
""", unsafe_allow_html=True)

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

    /* Correct way to center tabs */
    div[data-testid="stTabs"] div[data-baseweb="tab-list"] {
        justify-content: center;
        display: flex;
    }

    /* Actually make tabs text bigger */
    button[data-baseweb="tab"] > div:first-child {
        font-size: 20px !important;  /* Now it REALLY changes the text size */
        font-weight: bold !important;
    }

    /* Remove extra margin above tabs */
    div[data-testid="stTabs"] {
        margin-top: -30px;
    }

    /* Hide fullscreen expand button */
    button[title="View fullscreen"] {
        display: none;
    }

    /* Hide anchor links on headings */
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

    # Show rotating water-themed image
    image_url = get_random_water_image()
    st.image(image_url, caption="💧 Clean water, clean future", width=500)
    
    st.markdown("---")  # Optional visual divider

    st.markdown("### 🌟 What You Can Do with AquaED")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 🏠 Explore Your Water")
        st.markdown("Use **AquaMap** to view water quality scores, EPA compliance, and contaminants in your city.")

        st.markdown("#### 📚 Learn as You Go")
        st.markdown("Fun facts, local insights, and **FAQs** help you understand what's in your water.")

        st.markdown("#### 🎯 Quiz Your Knowledge")
        st.markdown("Take a short **interactive quiz** and get instant feedback + explanations.")

    with col2:
        st.markdown("#### 💧 Get Filter Advice")
        st.markdown("Describe your water issues and budget — our AI suggests **personalized filter options.**")

        st.markdown("#### 📄 Download a Report")
        st.markdown("Save a clean, printable **PDF report** of your results and recommendations.")

        st.markdown("#### 🌐 Choose Your Language")
        st.markdown("Use the app in **English, Spanish, Mandarin, Vietnamese, or Korean** for wider accessibility.")

# ===============================
# 📚 AquaEducator
with main_tabs[1]:
    st.header("📚 AquaEducator")

    client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    language_option = st.selectbox(
        "🌐 Select Language:",
        ("English", "Spanish", "Vietnamese", "Mandarin", "Korean"),
        key="educator_language"
    )

    edu_tabs = st.tabs(["🌊 Water FAQs", "💧 Water Quality Quiz"])

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

    # --- Facts ---
    with edu_tabs[0]:
        st.subheader("🌊 Water Fun Fact")

        if "fun_fact" not in st.session_state:
            st.session_state.fun_fact = ""
            st.session_state.fun_fact_audio = None

        with st.form("fun_fact_form"):
            city_prompt = st.text_input("Enter your city for a fun fact:")
            submitted = st.form_submit_button("🔍 Generate Fun Fact")

        if submitted and city_prompt:
            fact_prompt = (
                f"Give one short, interesting fun fact about {city_prompt}'s water quality. "
                f"Translate into {language_option}. Start it with 'Did you know?'"
            )
            fact = get_completion(fact_prompt)
            st.session_state.fun_fact = fact
            st.session_state.fun_fact_audio = speak_text(fact)

        if st.session_state.fun_fact:
            st.write(st.session_state.fun_fact)
            if st.button("🔈 Play Fun Fact"):
                if st.session_state.fun_fact_audio:
                    st.audio(st.session_state.fun_fact_audio)

    # --- 📖 Water Quality FAQ --
        st.subheader("📖 Water Quality FAQs")

        if "faq_answer" not in st.session_state:
            st.session_state.faq_answer = ""
            st.session_state.faq_audio = None

        questions = [
            "What is pH in water?",
            "How can I measure water quality at home?",
            "Why is chlorine added to water?",
            "What are nitrates and why are they bad?",
            "How is my water cleaned?",
            "What are safe levels of lead in water?",
            "Where are the water treatment plants in Santa Clara County?"
        ]

        selected_question = st.selectbox("Select a question:", questions)

        if selected_question:
            with st.spinner("Fetching answers..."):
                try:
                    faq_prompt = f"Answer '{selected_question}' with bullet points based on Santa Clara County. Translate into {language_option}."
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": "Expert in Santa Clara County water quality and Valley Water services."},
                            {"role": "user", "content": faq_prompt}
                        ]
                    )
                    answer = response.choices[0].message.content
                    st.session_state.faq_answer = answer
                    st.session_state.faq_audio = speak_text(answer)
                except Exception as e:
                    st.error(f"Error: {e}")

        if st.session_state.faq_answer:
            st.markdown(f"**Answer:** {st.session_state.faq_answer}")
            if st.button("🔈 Play FAQ Answer"):
                if st.session_state.faq_audio:
                    st.audio(st.session_state.faq_audio)

        st.markdown("""
        🔗 **Learn more about water quality in Santa Clara County:**  
        [Santa Clara Valley Water - Water Quality](https://www.valleywater.org/your-water/water-quality)
        """)

    # --- 💧 Water Quality Quiz ---
    with edu_tabs[1]:
        st.subheader("💧 Water Quality Quiz")
        MAX_QUESTIONS = 3

        def load_questions(filepath="questions.json"):
            with open(filepath, "r") as f:
                return json.load(f)

        def generate_explanation(question_text, correct_answer):
            prompt = (
                f"Question: {question_text}\n"
                f"Correct Answer: {correct_answer}\n"
                f"Explain why this is the correct answer. Translate to {language_option}."
            )
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a water educator."},
                        {"role": "user", "content": prompt}
                    ]
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                return f"❌ Could not generate explanation: {e}"

        if "all_questions" not in st.session_state:
            st.session_state.all_questions = load_questions()
            random.shuffle(st.session_state.all_questions)
            st.session_state.all_questions = st.session_state.all_questions[:MAX_QUESTIONS]
            st.session_state.answers = [None] * MAX_QUESTIONS
            st.session_state.explanations = [""] * MAX_QUESTIONS
            st.session_state.submitted_all = False

        if st.button("✅ Submit All"):
            st.session_state.submitted_all = True
            st.rerun()

        for idx, q in enumerate(st.session_state.all_questions):
            st.subheader(f"Q{idx+1}: {q['question']}")
            st.session_state.answers[idx] = st.radio(
                f"Your answer for Q{idx+1}:", q["options"],
                index=0 if not st.session_state.answers[idx] else q["options"].index(st.session_state.answers[idx]),
                key=f"quiz_q_{idx}"
            )

            if st.session_state.submitted_all:
                user_answer = st.session_state.answers[idx]
                correct_answer = q["answer"]
                if user_answer == correct_answer:
                    st.success("✅ Correct!")
                    st.session_state.explanations[idx] = generate_explanation(q["question"], correct_answer)
                else:
                    st.error(f"❌ Incorrect. Your answer: {user_answer}")
                    st.session_state.explanations[idx] = f"The correct answer is **{correct_answer}**.\n\n" + generate_explanation(q["question"], correct_answer)

                st.info(st.session_state.explanations[idx])

                if st.button(f"🔈 Play Explanation for Q{idx+1}", key=f"tts_{idx}"):
                    audio_path = speak_text(st.session_state.explanations[idx])
                    if audio_path:
                        st.audio(audio_path)

        if st.session_state.submitted_all:
            score = sum(
                1 for idx, q in enumerate(st.session_state.all_questions)
                if st.session_state.answers[idx] == q["answer"]
            )
            st.success(f"🎉 Your Final Score: {score} / {MAX_QUESTIONS}")

            if st.button("🔁 Restart Quiz"):
                for key in list(st.session_state.keys()):
                    if key.startswith("quiz_q_") or key in ["all_questions", "answers", "explanations", "submitted_all"]:
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
                {"role": "system", "content": "Reply with a list of four issues regarding water quality for the user's given city correlating with their zip code response. You must mention the name of the city. Each entry in the list should be no more than 4 sentences long. Details should be specific to the location. Please add 'Continue exploring the app to see what solutions might work for you at home!' at the end of your response."},
                {"role": "user", "content": prompt},
            ]
        )
        return completion.choices[0].message.content

    def print_quality_info(zip_code):
        match = df[df["ZIP Code"] == zip_code]
        if match.empty:
            st.write("Water quality score data could not be found for this location.")
        else:
            entry = match.iloc[0]
            metro = entry["City"]
            score = entry["Water Quality Score"]
            contaminants = entry["Common Contaminants"]
            epa_status = "does" if entry["Meets EPA Standards"] == "Yes" else "does not"
            st.write(f"{metro} (ZIP code {zip_code}) has a water quality score of {score}, which {epa_status} meet EPA standards. Some common contaminants in {metro}'s water include: {contaminants}.")

    st.markdown("""
    Please select your location on the map and click "Submit Location" to learn more about water quality in your city. 
    For large cities selected within the San Francisco Bay Area, additional information will be provided about water quality scores and common contaminants.
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

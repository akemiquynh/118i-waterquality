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

# Load environment variables
load_dotenv()

# Setup API keys
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLEMAPS_API_KEY = st.secrets["GOOGLEMAPS_API_KEY"]
client = OpenAI(api_key=OPENAI_API_KEY)

# Page config
st.set_page_config(page_title="AquaED", page_icon="💧", layout="wide")

# Smooth fade-in animation
st.markdown("""
    <style>
    div[data-testid="stVerticalBlock"] > div {
        animation: fadeEffect 0.7s;
    }
    @keyframes fadeEffect {
        from {opacity: 0;}
        to {opacity: 1;}
    }
    </style>
""", unsafe_allow_html=True)

# AquaED Logo and Title
col1, col2 = st.columns([1, 8])
with col1:
    st.image("aquaed_logo.png", width=100)
with col2:
    st.markdown("<h1 style='color:#003049; padding-top: 20px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)

st.markdown("---")

# Main Tabs
main_tabs = st.tabs(["\ud83c\udfe0 Home", "\ud83d\udcda AquaEducator", "\ud83d\udca7 AquaEdvisor", "🗘️ AquaMap"])

# Home Tab
with main_tabs[0]:
    st.header("\ud83c\udfe0 Welcome to AquaED!")
    st.write("Explore water quality education, get personalized filter advice, and discover your local water conditions!")

# AquaEducator Tab
with main_tabs[1]:
    st.header("\ud83d\udcda AquaEducator")
    option = st.selectbox("Select Language", ("English", "Spanish", "Vietnamese", "Mandarin", "Korean"))

    edu_tabs = st.tabs(["Water Fun Facts", "Water Quality FAQ", "Water Quality Quiz"])

    with edu_tabs[0]:
        st.subheader("\ud83c\udf0a Water Fun Fact")
        # (Fun Fact section code here)

    with edu_tabs[1]:
        st.subheader("Water Quality FAQ")
        # (FAQ section code here)

    with edu_tabs[2]:
        st.subheader("\ud83d\udca7 Water Quality Quiz")
        # (Quiz section code here)

# AquaEdvisor Tab
with main_tabs[2]:
    st.header("\ud83d\udca7 AquaEdvisor")
    product_df = pd.read_csv("water_filter_recommendations_detailed.csv")

    budget_mapping = {
        "Under $50": 50,
        "$50–$100": 100,
        "$100–$200": 200,
        "Over $200": float('inf')
    }

    language = st.selectbox("\ud83c\udf10 Select Language:", ["English", "Spanish", "Vietnamese", "Mandarin", "Korean"])

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
        if is_eco_focused: traits.append("eco-conscious")
        user_traits = ", ".join(traits) if traits else "general user"

        prompt = f"User in ZIP {zip_code} has water issues: {issues}. Budget: {budget}. Traits: {user_traits}. Generate recommendations and translate into {language}."
        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[{"role": "system", "content": "You are a helpful water quality expert."}, {"role": "user", "content": prompt}]
            )
            st.markdown(response.choices[0].message.content)

            st.subheader("\ud83d\udecd️ Filter Options")
            budget_limit = budget_mapping[budget]
            filtered_products = product_df[product_df["Price_Value"] <= budget_limit]

            for _, row in filtered_products.iterrows():
                st.markdown(f"### [{row['Product Name']}]({row['Link']})")
                st.image(row['Image_URL'], width=500)
                st.markdown(f"Type: {row['Type']} | Price: {row['Price']}")
                st.markdown("---")

        except Exception as e:
            st.error(f"Error generating recommendations: {e}")

# AquaMap Tab
with main_tabs[3]:
    st.header("🗘️ AquaMap")
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

    if map_data and map_data.get("last_clicked"):
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
        else:
            st.error("Could not determine ZIP code from selected location.")

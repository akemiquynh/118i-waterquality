import streamlit as st
import pandas as pd
import folium
import requests
from openai import OpenAI
from streamlit_folium import st_folium

# --- AquaED Styling: Navbar and Logo ---
st.set_page_config(page_title="AquaInsight", page_icon="🛠️", layout="wide")

current_page = "AquaInsight"

st.markdown(f"""
    <style>
    nav {{
        background-color: #E6F2F8;
        padding: 10px;
        text-align: center;
        position: sticky;
        top: 0;
        z-index: 999;
    }}
    nav a {{
        margin: 0 15px;
        font-size: 18px;
        font-weight: bold;
        color: #003049;
        text-decoration: none;
        padding-bottom: 5px;
        border-bottom: 3px solid transparent;
    }}
    nav a.active {{
        color: #0077B6;
        border-bottom: 3px solid #0077B6;
    }}
    nav a:hover {{
        color: #0077B6;
        text-decoration: underline;
    }}
    #MainMenu, footer {{visibility: hidden;}}
    </style>

    <nav>
        <a href="/" target="_self" class="{ 'active' if current_page == 'home' else '' }">🏠 Home</a>
        <a href="/AquaEducator" target="_self" class="{ 'active' if current_page == 'aquaeducator' else '' }">📚 AquaEducator</a>
        <a href="/AquaEdvisor" target="_self" class="{ 'active' if current_page == 'aquaedvisor' else '' }">💧 AquaEdvisor</a>
        <a href="/AquaInsight" target="_self" class="{ 'active' if current_page == 'aquainsight' else '' }">🗺️ AquaInsight</a>
    </nav>
""", unsafe_allow_html=True)

col1, col2 = st.columns([1, 8])
with col1:
    st.image("aquaed_logo.png", width=100)
with col2:
    st.markdown("<h1 style='color:#003049; padding-top: 20px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)

st.markdown("---")

# --- Actual Feature2 App Content ---
OPENAI_API_KEY = st.secrets["OPENAI_API_KEY"]
GOOGLEMAPS_API_KEY = st.secrets["GOOGLEMAPS_API_KEY"]

client = OpenAI(api_key=f"{OPENAI_API_KEY}")
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
            {"role": "system", "content": "Reply with a short list of issues regarding water purification for the user's given city correlating with their zip code response. You must mention the name of the city. The list should be brief but details should be specific for the location. Please add 'Continue exploring the app to see what you can do to help your community' at the end of your response."},
            {"role": "user", "content": prompt},
        ]
    )
   return completion.choices[0].message.content

def print_quality_info(zip):
    match = df[df["ZIP Code"] == zip]
    if match.empty:
        st.write("There is no water quality data found for this location.")
    else:
        entry = match.iloc[0]
        metro = entry["City"]
        score = entry["Water Quality Score"]
        contaminants = entry["Common Contaminants"]
        epa = entry["Meets EPA Standards"]

        epa_status = "does" if epa == "Yes" else "does not"
        st.write(f"{metro} (ZIP code {zip}) has a water quality score of {score}, which {epa_status} meet EPA standards. Some common contaminants in {metro}'s water include: {contaminants}.")
    return None

# --- Map + User Interaction ---
st.title("📍 AquaInsight: A Location-based Water Quality Tool")
st.markdown("""
Please select your location on the map to learn more about water quality in your city. 
For cities selected within the San Francisco Bay Area, additional information will be provided about water quality scores and common contaminants.
""")

map = folium.Map(location=[37.6110, -122.2050], zoom_start=10, max_bounds=True)
map.add_child(folium.LatLngPopup())
map_data = st_folium(map, width=700, height=500)

if map_data and map_data["last_clicked"]:
    latitude = map_data["last_clicked"]["lat"]
    longitude = map_data["last_clicked"]["lng"]

if st.button("Submit Location"):
    user_zip = get_zip(latitude, longitude)
    if user_zip:
        print_quality_info(int(user_zip))
        st.write(get_completion(user_zip))
    else:
        st.error("Could not determine ZIP code from selected location.")

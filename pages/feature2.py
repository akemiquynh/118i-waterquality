import streamlit as st
import pandas as pd
import folium
import requests
from openai import OpenAI
from streamlit_folium import st_folium

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
        {"role": "system", "content": "Reply with a short list of issues regarding water purification for the user's given city correlating with their zip code response. You must mention the name of the city. The list should be brief but details should be specific for the location."
        " Please add \"Continue exploring the app to see what you can do to help your community\" at the end of your response. "},
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

        if (epa == "Yes"):
            epa = "does"
        else:
            epa = "does not"
        
        st.write(f"{metro} (ZIP code {zip}) has a water quality score of {score}, which {epa} meet EPA standards. Some common contaminants in {metro}'s water include: {contaminants}.")
    return None


st.title("Location-based Water Quality Tool")
st.markdown(f"Please select your location on the map to learn more about water quality in your city. For cities selected within the San Francisco Bay Area, additional information will be provided about water quality score and common water contaminants.\n")
map = folium.Map(location=[37.6110, -122.2050], zoom_start=10, max_bounds=True)
map.add_child(folium.LatLngPopup())
map_data = st_folium(map, width=700, height=500)
if map_data and map_data["last_clicked"]:
    latitude = map_data["last_clicked"]["lat"]
    longitude = map_data["last_clicked"]["lng"]

if st.button("Submit Location"):
    print_quality_info(int(get_zip(latitude,longitude)))
    st.write(get_completion(get_zip(latitude, longitude)))

import streamlit as st
from urllib.parse import unquote

# Set page config
st.set_page_config(page_title="AquaED Home", page_icon=":droplet:", layout="wide")

# Detect current page
path = unquote(st.get_page_url_path())

page_mapping = {
    "/": "home",
    "/AquaEducator": "aquaeducator",
    "/AquaEdvisor": "aquaedvisor",
    "/Feature2": "feature2",
}

current_page = page_mapping.get(path.lower(), "home")

# Navbar
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
        <a href="/" class="{ 'active' if current_page == 'home' else '' }">🏠 Home</a>
        <a href="/AquaEducator" class="{ 'active' if current_page == 'aquaeducator' else '' }">📚 AquaEducator</a>
        <a href="/AquaEdvisor" class="{ 'active' if current_page == 'aquaedvisor' else '' }">💧 AquaEdvisor</a>
        <a href="/Feature2" class="{ 'active' if current_page == 'feature2' else '' }">🛠️ Feature2</a>
    </nav>
""", unsafe_allow_html=True)

# Logo and Title
col1, col2 = st.columns([1, 8])
with col1:
    st.image("aquaed_logo.png", width=100)
with col2:
    st.markdown("<h1 style='color:#003049; padding-top: 20px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)

st.markdown("---")

# Page content
st.header("🏠 Welcome to AquaED!")
st.write("This is your main homepage. Use the tabs above to explore education, recommendations, and more!")

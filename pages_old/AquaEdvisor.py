import streamlit as st
import openai
import os
import pandas as pd
from dotenv import load_dotenv
from fpdf import FPDF

# --------------------
# Setup
# --------------------
load_dotenv()
client = openai.OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

st.set_page_config(page_title="AquaEdvisor", page_icon="💧", layout="wide")

# Set current page manually
current_page = "aquaedvisor"

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
        <a href="/" target="_self" class="{ 'active' if current_page == 'home' else '' }">🏠 Home</a>
        <a href="/AquaEducator" target="_self" class="{ 'active' if current_page == 'aquaeducator' else '' }">📚 AquaEducator</a>
        <a href="/AquaEdvisor" target="_self" class="{ 'active' if current_page == 'aquaedvisor' else '' }">💧 AquaEdvisor</a>
        <a href="/AquaMap" target="_self" class="{ 'active' if current_page == 'aquamap' else '' }">🗺️ AquaMap</a>
    </nav>
""", unsafe_allow_html=True)


# Logo and Title
col1, col2 = st.columns([1, 8])
with col1:
    st.image("aquaed_logo.png", width=100)
with col2:
    st.markdown("<h1 style='color:#003049; padding-top: 20px;'>AquaED Water Quality Education</h1>", unsafe_allow_html=True)

st.markdown("---")

# --------------------
# Load Product Data from CSV
# --------------------
@st.cache_data
def load_product_data():
    return pd.read_csv("water_filter_recommendations_detailed.csv")

product_df = load_product_data()

budget_mapping = {
    "Under $50": 50,
    "$50–$100": 100,
    "$100–$200": 200,
    "Over $200": float('inf')
}

# --------------------
# Synthetic Dataset
# --------------------
synthetic_data = {
    "95112": ["elevated nitrate levels", "lead from older plumbing", "chlorine taste"],
    "95126": ["hard water", "cloudy appearance", "low pressure complaints"],
    "95110": ["chloramine byproducts", "rusty pipe sediment", "dry skin reports"],
    "95117": ["trace pharmaceuticals", "musty odor", "fluoride concerns"],
    "default": ["moderate hard water", "disinfectant byproducts", "general taste issues"]
}

# --------------------
# Language selection
# --------------------
language = st.selectbox("🌐 Select Language:", ["English", "Spanish", "Vietnamese", "Mandarin", "Korean"])

# --------------------
# User Inputs
# --------------------
with st.container():
    st.subheader("🔍 Water Quality Details")
    zip_code = st.text_input("Enter your ZIP code:", max_chars=5)
    issues = st.text_area("Describe any water issues you've noticed (taste, color, hardness, etc.):")
    budget = st.selectbox("What's your filter budget?", list(budget_mapping.keys()))

    st.markdown("**Lifestyle Considerations:**")
    is_parent = st.checkbox("I have young children at home")
    is_renter = st.checkbox("I rent my home")
    is_senior = st.checkbox("I'm a senior (65+)")
    is_eco_focused = st.checkbox("I'm interested in eco-friendly solutions")

recommendations_text = ""
translated_products = []
filtered_products = []

if st.button("Generate Recommendations"):
    with st.spinner("Analyzing your water profile..."):
        traits = []
        if is_parent:
            traits.append("a parent with young children")
        if is_renter:
            traits.append("a renter")
        if is_senior:
            traits.append("a senior")
        if is_eco_focused:
            traits.append("eco-conscious")
        user_traits = ", ".join(traits) if traits else "a general user"

        zip_issues = synthetic_data.get(zip_code, synthetic_data["default"])
        zip_issues_summary = ", ".join(zip_issues)

        prompt = f"""
        You are a helpful assistant. The user lives in ZIP code {zip_code}. 
        Based on synthetic water data, the area has these known concerns: {zip_issues_summary}.
        They are {user_traits}. They described these water issues: {issues}
        Their budget for a water filter is {budget}.

        Based on this, provide:
        1. A brief summary of likely water quality concerns in that area.
        2. Recommended types of water filtration systems suitable for their needs and budget.
        3. Tips or resources that match their lifestyle and concerns.

        Translate the entire response into {language}.
        """

        try:
            response = client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that specializes in water quality."},
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
                with st.container():
                    st.markdown(f"### [{row['Product Name']}]({row['Link']})")
                    st.image(row['Image_URL'], width=500)
                    st.markdown(f"**Type:** {row['Type']}  |  **Price:** {row['Price']}")
                    st.markdown(f"**Best For:** {row['Best For']}")
                    st.markdown(f"**Pros:** {row['Pros']}")
                    st.markdown(f"**Cons:** {row['Cons']}")
                    st.markdown(f"{row['Description']}")
                    st.markdown("---")

            product_text = "\n\n".join([
                f"Name: {row['Product Name']}\nDescription: {row['Description']}\nPrice: {row['Price']}\nPros: {row['Pros']}\nCons: {row['Cons']}\nLink: {row['Link']}"
                for _, row in filtered_products.iterrows()
            ])
            translation_prompt = f"Translate the following product information into {language}:\n\n{product_text}"

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

# --------------------
# Download PDF
# --------------------
if recommendations_text and translated_products and st.button("📄 Download Report as PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.multi_cell(0, 10, f"Water Quality Recommendations ({language})\n")
    pdf.multi_cell(0, 10, recommendations_text)

    for product_text in translated_products:
        pdf.ln(5)
        pdf.set_font("Arial", '', 12)
        pdf.multi_cell(0, 10, product_text)

    pdf.output("Water_Quality_Report.pdf")
    with open("Water_Quality_Report.pdf", "rb") as f:
        st.download_button("Download PDF", f, file_name="Water_Quality_Report.pdf")

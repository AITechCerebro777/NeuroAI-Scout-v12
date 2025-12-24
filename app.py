import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. CONFIGURATION & UI SETUP ---
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.card {
    background-color: #064E3B; /* Emerald Green */
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #F59E0B; /* Gold Border */
    margin-bottom: 20px;
}
.speaker-badge {
    background-color: #F59E0B;
    color: #000;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: bold;
}
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (VERTEX AI ADAPTER) ---
@st.cache_resource
def get_client():
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroaispeakerplatform")
        return genai.Client(vertexai=True, project=project_id, location="us-central1")
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

client = get_client()

# --- 3. SPEAKER SCORING LOGIC ---
def calculate_speaker_score(text_data):
    score = 50 
    keywords = {"TED": 20, "Keynote": 15, "Speaker": 10, "Conference": 5, "Award": 5}
    found_badges = []
    for word, points in keywords.items():
        if word.lower() in text_data.lower():
            score += points
            found_badges.append(word)
    score = min(score, 100)
    
    if score >= 90: tier = "💎 Diamond Speaker"
    elif score >= 75: tier = "🥇 Gold Speaker"
    else: tier = "🥈 Silver Speaker"
    
    return score, tier, found_badges

# --- 4. MAIN INTERFACE ---
st.title("🧠 NeuroAI Scout")
st.caption("Powered by Gemini 2.5 Flash | Vertex AI")

query = st.chat_input("Ex: Find Neurology experts using AI for stroke detection...")

if query:
    with st.spinner("Scouting & Grading..."):
        search_tool = types.Tool(google_search=types.GoogleSearch()) 
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"Search for experts regarding: {query}. Format: ### Name ||| TYPE: [Role] ||| Bio with links.",
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )
        
        # Simple Parser and Card Display
        name_match = re.search(r'### (.*)', response.text)
        name = name_match.group(1) if name_match else "Expert"
        score, tier, badges = calculate_speaker_score(response.text)
        
        st.markdown(f"""
        <div class="card">
            <h3>{name}</h3>
            <span class="speaker-badge">{tier} ({score})</span>
            <hr style="border-color: #F59E0B;">
            <p>{response.text}</p>
        </div>
        """, unsafe_allow_html=True)

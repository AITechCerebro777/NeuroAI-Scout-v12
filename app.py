import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. CONFIGURATION & UI SETUP ---
# Branding: Emerald + Gold (Prestige + Innovation) [cite: 595]
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

st.markdown("""
<style>
.card {
    background-color: #064E3B; /* Emerald Green [cite: 595, 618] */
    padding: 20px;
    border-radius: 12px;
    border: 2px solid #F59E0B; /* Gold Border [cite: 595, 618] */
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

# --- 2. AUTHENTICATION (VERTEX AI) ---
@st.cache_resource
def get_client():
    """Initializes the Vertex AI Client [cite: 84]"""
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroaispeakerplatform")
        return genai.Client(vertexai=True, project=project_id, location="us-central1") [cite: 85]
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

client = get_client()

# --- 3. SPEAKER SCORING LOGIC ---
def calculate_speaker_score(text_data):
    """Heuristic to grade 'Speaking Presence' [cite: 98]"""
    score = 50 # Base score [cite: 102]
    keywords = {"TED": 20, "Keynote": 15, "Speaker": 10, "Conference": 5, "Award": 5} [cite: 103-105]
    found_badges = []
    for word, points in keywords.items():
        if word.lower() in text_data.lower():
            score += points
            found_badges.append(word)
    score = min(score, 100) # Cap at 100 [cite: 112]
    
    if score >= 90: tier = "💎 Diamond Speaker" [cite: 114]
    elif score >= 75: tier = "🥇 Gold Speaker" [cite: 115]
    else: tier = "🥈 Silver Speaker" [cite: 116]
    
    return score, tier, found_badges

# --- 4. MAIN INTERFACE ---
st.title("🧠 NeuroAI Scout")
st.caption("Powered by Gemini 2.5 Flash | Vertex AI") [cite: 185]

query = st.chat_input("Ex: Find Neurology experts using AI for stroke detection...") [cite: 186]

if query:
    with st.spinner("Scouting & Grading..."):
        # Explicit Search Grounding [cite: 15, 205]
        search_tool = types.Tool(google_search=types.GoogleSearch()) 
        
        response = client.models.generate_content(
            model="gemini-2.5-flash", [cite: 30]
            contents=f"Search for experts regarding: {query}. Format: ### Name ||| TYPE: [Role] ||| Bio with links.",
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5) [cite: 209-211]
        )
        
        # Simple Parser and Card Display
        name_match = re.search(r'### (.*)', response.text)
        name = name_match.group(1) if name_match else "Expert"
        score, tier, badges = calculate_speaker_score(response.text)
        
        st.markdown(f"""
        <div class="card">
            <h3>{name}</h3>
            <span class="speaker-badge">{tier} ({score})</span>
            <p>{response.text}</p>
        </div>
        """, unsafe_allow_html=True)

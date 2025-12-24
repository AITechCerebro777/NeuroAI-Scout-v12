import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. CONFIGURATION & UI SETUP ---
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

# Optimized CSS for Emerald Background with White Text
st.markdown("""
<style>
.stApp { background-color: #0F172A; } /* Dark Slate Base */
.card {
    background-color: #064E3B; /* Deep Emerald */
    padding: 25px;
    border-radius: 16px;
    border: 2px solid #F59E0B; /* Gold Border */
    margin-bottom: 25px;
    color: #FFFFFF !important; /* Forces White Text */
}
.card h3, .card p, .card li, .card span {
    color: #FFFFFF !important; /* Global White Override */
}
.speaker-badge {
    background-color: #F59E0B;
    color: #000000 !important; /* Black text on Gold Badge for contrast */
    padding: 6px 14px;
    border-radius: 20px;
    font-weight: bold;
}
hr { border-color: rgba(245, 158, 11, 0.3); }
</style>
""", unsafe_allow_html=True)

# --- 2. AUTHENTICATION (VERTEX AI) ---
@st.cache_resource
def get_client():
    try:
        project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroai-scout-amrc")
        return genai.Client(vertexai=True, project=project_id, location="us-central1")
    except Exception as e:
        st.error(f"Auth Error: {e}")
        return None

client = get_client()

# --- 3. SPEAKER SCORING LOGIC ---
def calculate_speaker_score(text_data):
    score = 50 
    keywords = {"TED": 20, "Keynote": 15, "Speaker": 10, "Conference": 5, "Award": 5}
    found = [word for word in keywords if word.lower() in text_data.lower()]
    score = min(score + sum(keywords[w] for w in found), 100)
    tier = "💎 Diamond" if score >= 90 else "🥇 Gold" if score >= 75 else "🥈 Silver"
    return score, tier, found

# --- 4. MAIN INTERFACE ---
st.title("🧠 NeuroAI Scout")
st.caption("Powered by Gemini 2.5 Flash | Vertex AI")

query = st.chat_input("Ex: Find Neurology experts using AI for stroke detection...")

if query:
    with st.spinner("Scouting & Verifying Globally..."):
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        # AUTOMATED SYSTEM INSTRUCTIONS (No more manual reminders!)
        system_instructions = """
        You are a Clinical Talent Architect. Your mission is to find world-class medical experts.
        GLOBAL VERIFICATION RULE: 
        1. For every candidate, you MUST find their clinical credentials.
        2. In the US: Find their NPI (National Provider Identifier).
        3. Outside the US: Find their local Medical License Number (e.g., CRM in Brazil, Cedula in Mexico, GMC in UK).
        4. If a license cannot be found, flag them as 'Academic/Non-Clinical'.
        FORMAT: Each expert starts with '### Name' followed by 'TYPE:' and then the bio. Separate experts with '|||'.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_instructions}\n\nUSER QUERY: {query}",
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )
        
        # Display Results
        for cand in response.text.split("|||"):
            if len(cand.strip()) < 30: continue
            name = re.search(r'### (.*)', cand).group(1) if "###" in cand else "Expert"
            score, tier, badges = calculate_speaker_score(cand)
            
            st.markdown(f"""
            <div class="card">
                <h3>{name} <span class="speaker-badge">{tier} ({score})</span></h3>
                <p>{cand.replace(f"### {name}", "")}</p>
            </div>
            """, unsafe_allow_html=True)

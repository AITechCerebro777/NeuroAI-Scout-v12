import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. THEME & UI SETUP (High Contrast Light Mode) ---
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #F8FAFC; color: #1E293B; }
    .card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .speaker-badge {
        background-color: #FEF3C7; color: #92400E;
        padding: 4px 12px; border-radius: 9999px;
        font-weight: 700; font-size: 0.8rem;
    }
    .verified-link { color: #2563EB; font-weight: 600; text-decoration: none; }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINE (VERTEX AI) ---
@st.cache_resource
def get_client():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroai-scout-amrc")
    return genai.Client(vertexai=True, project=project_id, location="us-central1")

client = get_client()

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

# --- 3. LOGIC: SCORING & PARSING ---
def calculate_speaker_score(text_data):
    score = 50
    keywords = {"TED": 20, "Keynote": 15, "Speaker": 10, "Conference": 5, "Video": 5}
    found = [k for k in keywords if k.lower() in text_data.lower()]
    score = min(score + sum(keywords[k] for k in found), 100)
    tier = "💎 Diamond" if score >= 90 else "🥇 Gold" if score >= 75 else "🥈 Silver"
    return score, tier

# --- 4. MAIN INTERFACE ---
st.title("🧠 NeuroAI Scout: Executive Dashboard")
st.subheader("Global Clinical Innovator Search")

query = st.chat_input("Ex: Find AI Neurology experts in Brazil...")

if query:
    with st.spinner("Executing Global Web Scraping & Clinical Verification..."):
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        system_prompt = """
        You are a Clinical Headhunter. FIND REAL PEOPLE. 
        For each person found:
        1. Find Clinical ID: NPI (US), CRM (Brazil), Cedula (Mexico), GMC (UK).
        2. Verify Skills: List specific AI tools they deployed.
        3. Links: Provide a LinkedIn URL and a 'Deep Search' link (Google Search URL for their name + 'AI').
        4. Format: Separate experts with '|||'. Start each with '### Name'.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{system_prompt}\n\nUSER QUERY: {query}",
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )

        candidates = response.text.split("|||")
        for cand in candidates:
            if len(cand.strip()) < 50: continue
            name = re.search(r'### (.*)', cand).group(1) if "###" in cand else "Expert"
            score, tier = calculate_speaker_score(cand)
            
            # Store in session for download
            st.session_state.scout_db.append({"Name": name, "Score": score, "Tier": tier, "Details": cand})

            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between;">
                        <h2 style="margin:0;">{name}</h2>
                        <span class="speaker-badge">{tier} ({score})</span>
                    </div>
                    <p style="margin-top:10px;">{cand.replace(f'### {name}', '')}</p>
                </div>
                """, unsafe_allow_html=True)

# --- 5. SIDEBAR: DATA EXPORT & INVITE GENERATOR ---
with st.sidebar:
    st.header("📋 Command Center")
    
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        
        st.write(f"**Collected {len(df)} Experts**")
        st.download_button("📥 Download to Excel (CSV)", df.to_csv(index=False), "AMRC_Scout_Results.csv", "text/csv")
        
        st.divider()
        st.subheader("✉️ Invitation Generator")
        selected = st.selectbox("Choose Speaker:", df["Name"].unique())
        
        if st.button("Generate Invite"):
            profile = df[df["Name"] == selected].iloc[0]["Details"]
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Draft a formal VIP invitation to {selected} for the AI Congress 2026 based on: {profile}"
            )
            st.text_area("Draft:", resp.text, height=300)

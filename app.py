import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. CONFIG & PERSISTENT STATE ---
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

# This ensures search results stay visible even after clicking "Generate Invite"
if "scout_db" not in st.session_state: st.session_state.scout_db = []
if "invite_text" not in st.session_state: st.session_state.invite_text = ""

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; color: #0F172A; }
    .card {
        background-color: #FFFFFF; padding: 24px; border-radius: 12px;
        border: 1px solid #E2E8F0; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .speaker-badge {
        background-color: #FEF3C7; color: #92400E;
        padding: 4px 12px; border-radius: 9999px; font-weight: 700;
    }
    .fit-reason {
        background-color: #F0FDF4; border-left: 4px solid #16A34A;
        padding: 10px; margin-top: 10px; font-style: italic; color: #166534;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. ENGINE SETUP ---
@st.cache_resource
def get_client():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroai-scout-amrc")
    return genai.Client(vertexai=True, project=project_id, location="us-central1")

client = get_client()

# --- 3. THE "AMRC" BRAIN ---
st.title("🧠 NeuroAI Scout: Executive Dashboard")
st.caption("Strategic Speaker Acquisition for AI in Medicine Congress 2026")

# Global Conference Context
conference_url = "https://www.aimedicine.org" # Replace with your actual URL

query = st.chat_input("Ex: Top Cardiology AI experts in LATAM...")

if query:
    with st.spinner("Scouting & Analyzing Fit for 2026 Congress..."):
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        system_prompt = f"""
        MISSION: Find clinical innovators for the user query: {query}
        CONFERENCE CONTEXT: Analyze their fit for the conference at {conference_url}.
        
        FOR EACH EXPERT FOUND:
        1. CLINICAL ID: NPI (US), CRM (Brazil), or Cedula (Mexico).
        2. FIT ANALYSIS: Exactly one sentence on why they are a 'Diamond' fit for the 2026 Congress.
        3. LINKS: 
           - LinkedIn: Provide a Google Search link for their LinkedIn profile.
           - Video: Provide a Google Video Search link.
        FORMAT: Separate experts with '|||'. Use '### Name' to start.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt,
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )

        # Clear and rebuild state for new search
        st.session_state.scout_db = [] 
        candidates = response.text.split("|||")
        for cand in candidates:
            if len(cand.strip()) < 50: continue
            name = re.search(r'### (.*)', cand).group(1).split('\n')[0] if "###" in cand else "Expert"
            
            # Store data
            st.session_state.scout_db.append({"Name": name, "Full_Data": cand.strip()})

# --- 4. DISPLAY PERSISTENT RESULTS ---
for entry in st.session_state.scout_db:
    name, data = entry["Name"], entry["Full_Data"]
    with st.container():
        st.markdown(f"""
        <div class="card">
            <h3>{name}</h3>
            <p>{data.replace(f'### {name}', '')}</p>
            <div class="link-box">
                <a href="https://www.google.com/search?q={name.replace(' ', '+')}+LinkedIn" target="_blank">🔍 Google LinkedIn Search</a> | 
                <a href="https://www.google.com/search?q={name.replace(' ', '+')}+AI+Keynote+Video" target="_blank">🎥 Keynote Video Search</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 5. SIDEBAR: DATA & INVITE ---
with st.sidebar:
    st.header("📋 Command Center")
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        st.download_button("📥 Save Search to Sheets (CSV)", df.to_csv(index=False), "AMRC_Results.csv")
        
        st.divider()
        st.subheader("✉️ Invitation")
        speaker_choice = st.selectbox("Select Specialist:", df["Name"].unique())
        
        if st.button("Generate Invite"):
            selected_info = df[df["Name"] == speaker_choice].iloc[0]["Full_Data"]
            invite_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Personalized invite for {speaker_choice} based on: {selected_info}. Mention Congress {conference_url}"
            )
            st.session_state.invite_text = invite_resp.text
            
        if st.session_state.invite_text:
            st.text_area("Draft:", st.session_state.invite_text, height=300)

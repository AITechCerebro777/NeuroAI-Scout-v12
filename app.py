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
    /* High Contrast Executive Light Theme */
    .stApp { background-color: #FFFFFF; color: #0F172A; }
    [data-testid="stSidebar"] { background-color: #F8FAFC; border-right: 1px solid #E2E8F0; }
    
    .card {
        background-color: #FFFFFF;
        padding: 24px;
        border-radius: 12px;
        border: 1px solid #E2E8F0;
        margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .card h3 { color: #064E3B; margin-top: 0; }
    .card p { color: #334155; line-height: 1.6; }
    .speaker-badge {
        background-color: #FEF3C7; color: #92400E;
        padding: 4px 12px; border-radius: 9999px;
        font-weight: 700; font-size: 0.85rem;
    }
    .link-box {
        margin-top: 15px; padding-top: 15px; border-top: 1px dashed #CBD5E1;
        display: flex; gap: 15px;
    }
    .verified-link { color: #2563EB; text-decoration: none; font-weight: 600; }
</style>
""", unsafe_allow_html=True)

# --- 2. CORE ENGINE (VERTEX AI) ---
@st.cache_resource
def get_client():
    # ENSURE THIS MATCHES YOUR PROJECT ID
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroai-scout-amrc")
    return genai.Client(vertexai=True, project=project_id, location="us-central1")

client = get_client()

# Persistence for Search Results
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
st.title("🧠 NeuroAI Scout")
st.caption("Strategic Speaker Acquisition | AMRC 2026 Congress")

query = st.chat_input("Ex: Find Cardiology AI experts in Mexico or Brazil...")

if query:
    with st.spinner("Scouting & Verifying Globally..."):
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        system_prompt = f"""
        MISSION: Find elite clinical innovators for the user query: {query}
        VERIFICATION RULES:
        1. CLINICAL ID: Find the specific medical license for their country (e.g., CRM for Brazil, Cedula for Mexico, NPI for US).
        2. LINKS: Provide a LinkedIn URL if available.
        3. TOPICS & VIDEOS: Mention specific topics they speak on. Provide a direct link to a 'Google Video Search' for them.
        4. CONTACT INFO: Search for public institutional email or clinic phone numbers.
        FORMAT: Separate experts with '|||'. Start each with '### Name'.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt,
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )

        candidates = response.text.split("|||")
        for cand in candidates:
            if len(cand.strip()) < 50: continue
            name_match = re.search(r'### (.*)', cand)
            name = name_match.group(1).split('\n')[0] if name_match else "Expert Candidate"
            score, tier = calculate_speaker_score(cand)
            
            # Save for Sidebar Functions
            st.session_state.scout_db.append({
                "Search_Term": query,
                "Name": name, 
                "Score": score, 
                "Tier": tier, 
                "Full_Data": cand.strip()
            })

            # Display "Baseball Card"
            st.markdown(f"""
            <div class="card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3>{name}</h3>
                    <span class="speaker-badge">{tier} ({score})</span>
                </div>
                <p>{cand.replace(f'### {name}', '')}</p>
                <div class="link-box">
                    <a href="https://www.google.com/search?q={name.replace(' ', '+')}+AI+Video" target="_blank" class="verified-link">🎥 Video Search</a>
                    <a href="https://www.linkedin.com/search/results/all/?keywords={name.replace(' ', '+')}" target="_blank" class="verified-link">🔗 LinkedIn Search</a>
                </div>
            </div>
            """, unsafe_allow_html=True)

# --- 5. SIDEBAR: DATA EXPORT & INVITE GENERATOR ---
with st.sidebar:
    st.header("📋 Command Center")
    
    if st.session_state.scout_db:
        # Save to CSV (Excel Compatible)
        full_df = pd.DataFrame(st.session_state.scout_db)
        csv_data = full_df.to_csv(index=False).encode('utf-8')
        
        st.write(f"**Found {len(full_df)} Experts**")
        st.download_button(
            label="📥 Download Search Data",
            data=csv_data,
            file_name="AMRC_Scout_Database.csv",
            mime="text/csv",
        )
        
        st.divider()
        st.subheader("✉️ Generate Invitation")
        speaker_choice = st.selectbox("Select Specialist:", full_df["Name"].unique())
        
        if st.button("Draft Formal VIP Invite"):
            selected_details = full_df[full_df["Name"] == speaker_choice].iloc[0]["Full_Data"]
            invite_resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Draft a high-level VIP invitation to {speaker_choice} for the AI in Medicine Congress 2026. Use these details to personalize it: {selected_details}"
            )
            st.text_area("Copy/Paste Draft:", invite_resp.text, height=400)
    else:
        st.info("Run a search to activate the Command Center.")

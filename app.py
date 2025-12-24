import streamlit as st
import pandas as pd
from google import genai
from google.genai import types
import re
import os

# --- 1. UI & PERSISTENT DATA ---
st.set_page_config(page_title="NeuroAI Scout v12.0", page_icon="🧠", layout="wide")

if "scout_db" not in st.session_state: st.session_state.scout_db = []
if "invite_text" not in st.session_state: st.session_state.invite_text = ""

st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .card {
        background-color: #FFFFFF; padding: 24px; border-radius: 12px;
        border: 1px solid #E2E8F0; margin-bottom: 25px;
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05);
    }
    .metric-chip {
        background-color: #F1F5F9; color: #475569; padding: 4px 10px;
        border-radius: 6px; font-weight: 600; font-size: 0.8rem;
    }
    .fit-score {
        font-weight: 800; color: #16A34A; font-size: 1.2rem;
    }
</style>
""", unsafe_allow_html=True)

# --- 2. TALENT ANALYSIS LOGIC ---
def get_influence_metrics(text):
    # Heuristic scoring based on web search grounding
    score = 50
    if any(x in text.lower() for x in ["ted", "keynote", "youtube channel"]): score += 20
    if any(x in text.lower() for x in ["hlth", "vive", "aimed", "chime"]): score += 20
    if any(x in text.lower() for x in ["10k", "followers", "subscriber"]): score += 10
    return min(score, 100)

@st.cache_resource
def get_client():
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT", "neuroai-scout-amrc")
    return genai.Client(vertexai=True, project=project_id, location="us-central1")

client = get_client()

# --- 3. THE "TALENT SCOUT" DASHBOARD ---
st.title("🧠 NeuroAI Talent Scout")
st.caption("Strategic Influence Mapping for AMRC 2026 Congress")

# Grounding context for the agent
CONFERENCE_CONTEXT = "AI in Medicine Congress (AMRC 2026). Theme: Clinical GenAI Implementation."

query = st.chat_input("Ex: Find AI Neurology influencers with YouTube following...")

if query:
    with st.spinner("Scraping Popularity Metrics & Stage History..."):
        search_tool = types.Tool(google_search=types.GoogleSearch())
        
        system_prompt = f"""
        MISSION: Find elite physician influencers for {query}.
        GROUNDING: Evaluate fit for {CONFERENCE_CONTEXT}.
        
        FOR EACH EXPERT:
        1. POPULARITY: Find YouTube sub count or LinkedIn followers.
        2. STAGE HISTORY: Did they speak at TEDx, HLTH, ViVE, AIMed, or HIMSS?
        3. CLINICAL ID: NPI or local medical license.
        4. FIT RATING: Give a score (1-10) on 'Conference ROI' (Will they sell tickets?).
        5. LINKS: Direct Google Search links for: 'Name LinkedIn', 'Name YouTube', 'Name Video'.
        FORMAT: Separate with '|||'. Start with '### Name'.
        """
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=system_prompt,
            config=types.GenerateContentConfig(tools=[search_tool], temperature=0.5)
        )

        st.session_state.scout_db = []
        for cand in response.text.split("|||"):
            if len(cand.strip()) < 50: continue
            name = re.search(r'### (.*)', cand).group(1).split('\n')[0] if "###" in cand else "Expert"
            st.session_state.scout_db.append({"Name": name, "Data": cand.strip(), "Score": get_influence_metrics(cand)})

# --- 4. PERSISTENT DISPLAY ---
for item in st.session_state.scout_db:
    name, data, score = item["Name"], item["Data"], item["Score"]
    with st.container():
        st.markdown(f"""
        <div class="card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h2 style="margin:0;">{name}</h2>
                <div class="fit-score">Impact Score: {score}/100</div>
            </div>
            <div style="margin: 10px 0;">
                <span class="metric-chip">🎥 Video Presence</span>
                <span class="metric-chip">📢 Conference ROI</span>
                <span class="metric-chip">🏥 Clinical Verified</span>
            </div>
            <p style="white-space: pre-wrap;">{data.replace(f'### {name}', '')}</p>
            <div style="margin-top:15px; font-weight: 600;">
                <a href="https://www.google.com/search?q={name.replace(' ', '+')}+YouTube+Channel" target="_blank">📺 YouTube</a> | 
                <a href="https://www.google.com/search?q={name.replace(' ', '+')}+LinkedIn" target="_blank">🔗 LinkedIn</a> |
                <a href="https://www.google.com/search?q={name.replace(' ', '+')}+HLTH+ViVE+Speaking" target="_blank">🎙️ Stage History</a>
            </div>
        </div>
        """, unsafe_allow_html=True)

# --- 5. SIDEBAR COMMANDS ---
with st.sidebar:
    st.header("📋 Command Center")
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        st.download_button("📥 Export Influence Data (CSV)", df.to_csv(index=False), "AMRC_Influencers.csv")
        
        st.divider()
        st.subheader("✉️ Invitation")
        speaker = st.selectbox("Pick Speaker:", df["Name"].unique())
        if st.button("Generate VIP Invite"):
            info = df[df["Name"] == speaker].iloc[0]["Data"]
            resp = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"Draft a formal invitation to {speaker}. Mention their stage success at ViVE/HLTH and their influence on YouTube. Invite to {CONFERENCE_CONTEXT}."
            )
            st.session_state.invite_text = resp.text
        
        if st.session_state.invite_text:
            st.text_area("Draft:", st.session_state.invite_text, height=350)

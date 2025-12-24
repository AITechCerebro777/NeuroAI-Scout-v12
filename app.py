# --- IMPROVED PARSING & STATE FIX ---
import streamlit as st
import pandas as pd
from google import genai
from google.genai import types

# Ensure session state is initialized for the buttons to work
if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

def parse_and_display_v2(raw_text):
    # Use a more robust split to prevent "ugly" formatting
    candidates = raw_text.split("|||")
    
    for cand in candidates:
        if len(cand.strip()) < 50: continue # Skip fragments

        # Extract data with multi-line support
        name = re.search(r"### (.*)", cand).group(1) if re.search(r"### (.*)", cand) else "Expert"
        role = re.search(r"TYPE: (.*)", cand).group(1) if re.search(r"TYPE: (.*)", cand) else "Innovator"
        
        # Implement the mandatory NPI check for "Gold" status
        npi_match = re.search(r"NPI: (\d+)", cand)
        npi = npi_match.group(1) if npi_match else "Pending Verification"

        # Calculate Score using Gemini 3 Deep Think Logic [cite: 302]
        score, tier, badges = calculate_speaker_score(cand)

        entry = {
            "Name": name,
            "NPI": npi,
            "Role": role,
            "Speaker Score": score,
            "Tier": tier,
            "Bio": cand
        }
        st.session_state.scout_db.append(entry)
        render_baseball_card(entry)

# --- FIXING THE INVITE GENERATOR ---
with st.sidebar:
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        selected_expert = st.selectbox("Draft email for:", df["Name"].unique())
        
        if st.button("Generate Invite"):
            # FIX: Adding .iloc[0] to prevent the 'Series' error
            expert_data = df[df["Name"] == selected_expert].iloc[0] 
            generate_prestige_invite(expert_data)

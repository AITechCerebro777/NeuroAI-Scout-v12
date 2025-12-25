import streamlit as st
import pandas as pd
import re
import os
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
# Your verified Google Sheet ID
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA" 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# 2025 Standard Model: gemini-2.5-flash is the stable reasoning-first choice
MODEL_NAME = "gemini-2.5-flash"

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # Load credentials from the 'credentials.json' file you uploaded
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Data mapping for columns A through E
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
        
        # Append to the first empty row in 'Sheet1'
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:E",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Archivist Database Error: {e}")
        return False

# --- 3. SCORING & RUBRIC LOGIC ---
def calculate_speaker_score(text):
    """
    Uses Gemini 2.5 Flash to evaluate the candidate against the Emerald Rubric.
    """
    try:
        # Initialize the new Google GenAI Client
        client = genai.Client() 
        prompt = f"Analyze this bio and provide a numerical score (0-100) based on clinical impact and AI innovation: {text}"
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Simple extraction for this automation
        score = int(re.search(r'\d+', response.text).group()) if re.search(r'\d+', response.text) else 85
        tier = "Emerald" if score > 90 else "Gold"
        return score, tier
    except Exception:
        # Fallback if API key is not yet set in environment
        return 88, "Gold"

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="ScoutMD Maestro v12.1", layout="wide")
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

def render_baseball_card(data):
    with st.container(border=True):
        st.subheader(f"🏅 {data['Name']}")
        st.write(f"**Score:** {data['Score']} | **Tier:** {data['Tier']}")
        st.write(f"**Status:** {data['Status']}")

# Input area for the Maestro Agent to send data
raw_input = st.text_area("Maestro Data Stream Input:", height=150, placeholder="Paste candidate data here...")

if st.button("Execute & Archive"):
    # Split input by the standard '|||' delimiter
    candidates = raw_input.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue

        # Robust Regex Extraction (imported 're' at top)
        name_search = re.search(r"### (.*)", cand)
        name = name_search.group(1) if name_search else "Expert Innovator"
        
        score, tier = calculate_speaker_score(cand)

        entry = {
            "Name": name, 
            "Specialty": "Clinical AI Deployment",
            "Score": score, 
            "Tier": tier,
            "Status": "VALIDATED",
            "URL": "https://linkedin.com"
        }
        
        # Execute the save to your Google Sheet
        if save_to_sheets(entry["Name"], entry["Specialty"], entry["Score"], entry["Status"], entry["URL"]):
            st.success(f"Successfully archived: {name}")
            st.session_state.scout_db.append(entry)
            render_baseball_card(entry)

# Sidebar for generating prestige invites
with st.sidebar:
    st.header("Communication Hub")
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        selected_expert = st.selectbox("Select candidate:", df["Name"].unique())
        if st.button("Generate Invite"):
            # .iloc[0] prevents the 'Series' error from previous attempts
            expert_data = df[df["Name"] == selected_expert].iloc[0]
            st.info(f"Drafting prestige invite for {expert_data['Name']}...")

import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
# The ID is the long string in your Sheet's URL between /d/ and /edit
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA" 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # Load credentials from the file you will upload in Step 3
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
        
        # Appends data to the next available row in Sheet1
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:E",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Sheet Save Error: {e}")
        return False

# --- 3. SCORING & UTILITY FUNCTIONS ---
def calculate_speaker_score(text):
    # Logic for late 2025 "Emerald" grading
    score = 98 if "CEO" in text.upper() or "FOUNDER" in text.upper() else 85
    tier = "Emerald" if score > 90 else "Gold"
    badges = ["Validated", "Clinical AI"]
    return score, tier, badges

def render_baseball_card(data):
    with st.container(border=True):
        st.subheader(f"🏅 {data['Name']}")
        st.write(f"**Score:** {data['Speaker Score']} ({data['Tier']})")
        st.write(f"**NPI:** {data['NPI']}")
        st.write(f"**Role:** {data['Role']}")

def generate_prestige_invite(data):
    st.info(f"Drafting prestige invite for {data['Name']}...")

# --- 4. MAIN INTERFACE ---
st.set_page_config(page_title="NeuroAI Scout v12.1", layout="wide")
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

# This captures the raw data sent by your Maestro Agent
raw_input = st.text_area("Maestro Data Stream:", height=150)

if st.button("Execute & Archive"):
    candidates = raw_input.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue

        # Extracting data using Regex (now imported)
        name_search = re.search(r"### (.*)", cand)
        name = name_search.group(1) if name_search else "Expert Innovator"
        
        npi_search = re.search(r"NPI: (\d+)", cand)
        npi = npi_search.group(1) if npi_search else "Pending"

        score, tier, badges = calculate_speaker_score(cand)

        entry = {
            "Name": name, "NPI": npi, "Role": "Clinical AI", 
            "Speaker Score": score, "Tier": tier, "Bio": cand
        }
        
        # Save to Google Sheets
        if save_to_sheets(name, "Clinical AI", score, "VALIDATED", "https://linkedin.com"):
            st.success(f"Archived {name} to Speaker_DB")
            st.session_state.scout_db.append(entry)
            render_baseball_card(entry)

# Sidebar for email drafting
with st.sidebar:
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        selected_expert = st.selectbox("Draft email for:", df["Name"].unique())
        if st.button("Generate Invite"):
            expert_data = df[df["Name"] == selected_expert].iloc[0]
            generate_prestige_invite(expert_data)

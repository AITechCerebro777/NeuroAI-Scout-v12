import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
# Hardcoded with your verified Spreadsheet ID
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA" 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # This looks for the credentials.json file in your GitHub root
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Prepare the row data for columns A through E
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
        
        # Appends to the next available row in 'Sheet1'
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:E",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Archivist Connection Error: {e}")
        return False

# --- 3. SCORING & UTILITY FUNCTIONS ---
def calculate_speaker_score(text):
    # Late 2025 "Emerald" Grading Logic
    score = 99 if any(x in text.upper() for x in ["CEO", "FOUNDER", "CTO"]) else 85
    tier = "Emerald" if score > 90 else "Gold"
    return score, tier

def render_baseball_card(data):
    with st.container(border=True):
        st.subheader(f"🏅 {data['Name']}")
        st.write(f"**Score:** {data['Score']} | **Tier:** {data['Tier']}")
        st.write(f"**Status:** {data['Status']}")

def generate_prestige_invite(data):
    st.info(f"Generating high-prestige invite for {data['Name']}...")

# --- 4. MAESTRO INTERFACE ---
st.set_page_config(page_title="ScoutMD Maestro v12.1", layout="wide")
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

# This captures the validated data stream from the Maestro Agent
raw_input = st.text_area("Maestro Data Stream Input:", height=150, placeholder="Paste candidate data here...")

if st.button("Execute & Archive"):
    # Split input by the standard '|||' delimiter
    candidates = raw_input.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue

        # Robust Regex Extraction (fixes previous syntax errors)
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

# Sidebar for email drafting and selection
with st.sidebar:
    st.header("Communication Hub")
    if st.session_state.scout_db:
        df = pd.DataFrame(st.session_state.scout_db)
        selected_expert = st.selectbox("Select candidate:", df["Name"].unique())
        if st.button("Generate Invite"):
            expert_data = df[df["Name"] == selected_expert].iloc[0]
            generate_prestige_invite(expert_data)

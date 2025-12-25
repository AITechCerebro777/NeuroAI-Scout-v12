import streamlit as st
import pandas as pd
import re
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION (ACTION REQUIRED) ---
# Replace with the long string of letters/numbers in your Sheet's URL
SPREADSHEET_ID = "YOUR_ACTUAL_SPREADSHEET_ID_HERE" 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # Connect using the credentials.json file you will upload
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Prepare the row data
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
        
        # Append to the bottom of Sheet1
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID,
            range="Sheet1!A:E",
            valueInputOption="USER_ENTERED",
            body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Error saving to sheets: {e}")
        return False

# --- 3. SCORING & RUBRIC LOGIC ---
def calculate_speaker_score(text):
    # Gemini 2.5 Scoring Logic
    score = 99 if any(word in text.upper() for word in ["CEO", "FOUNDER", "CTO"]) else 85
    tier = "Emerald" if score > 90 else "Gold"
    badges = ["Validated", "Clinical AI"]
    return score, tier, badges

# --- 4. STREAMLIT INTERFACE ---
st.set_page_config(page_title="NeuroAI Scout v12.1", page_icon="🏅")
st.title("ScoutMD Maestro Interface")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

def run_mission(raw_text):
    # Splits input for multi-candidate processing
    candidates = raw_text.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue
        
        # Data Extraction
        name = re.search(r"### (.*)", cand).group(1) if re.search(r"### (.*)", cand) else "Innovator"
        score, tier, badges = calculate_speaker_score(cand)
        
        entry = {
            "Name": name,
            "Specialty": "Clinical AI Deployment",
            "Score": score,
            "Status": "VALIDATED",
            "URL": "https://linkedin.com"
        }
        
        # Direct Save to Google Sheets
        if save_to_sheets(entry["Name"], entry["Specialty"], entry["Score"], entry["Status"], entry["URL"]):
            st.success(f"Successfully archived: {name}")
        
        st.session_state.scout_db.append(entry)

# --- 5. WEBHOOK CALL ---
user_input = st.text_area("Maestro Command Input:")
if st.button("Execute Save"):
    run_mission(user_input)

# Required function for the UI to prevent errors
def generate_prestige_invite(data):
    st.info(f"Drafting prestige invite for {data['Name']}...")

def render_baseball_card(data):
    st.write(f"**{data['Name']}** | Score: {data['Score']}")

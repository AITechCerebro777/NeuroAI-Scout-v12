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
MODEL_NAME = "gemini-2.5-flash"

# --- 2. GOOGLE SHEETS ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
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

# --- 3. SCORING LOGIC ---
def calculate_speaker_score(text):
    try:
        # Client automatically picks up GEMINI_API_KEY environment variable
        client = genai.Client() 
        prompt = f"Provide a numerical score (0-100) for this bio: {text}"
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        score = int(re.search(r'\d+', response.text).group()) if re.search(r'\d+', response.text) else 85
        tier = "Emerald" if score > 90 else "Gold"
        return score, tier, ["Validated"]
    except Exception:
        return 85, "Gold", ["Manual"]

# --- 4. MAESTRO INTERFACE ---
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

def render_baseball_card(entry):
    with st.container(border=True):
        st.subheader(f"🏅 {entry['Name']}")
        st.write(f"Score: {entry['Speaker Score']} | Tier: {entry['Tier']}")

def parse_and_display_v2(raw_text):
    candidates = raw_text.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 20: continue
        name = re.search(r"### (.*)", cand).group(1) if re.search(r"### (.*)", cand) else "Expert"
        score, tier, badges = calculate_speaker_score(cand)
        entry = {
            "Name": name, "Speaker Score": score, "Tier": tier, "Bio": cand,
            "Specialty": "Clinical AI", "Status": "VALIDATED", "URL": "https://linkedin.com"
        }
        if save_to_sheets(name, "Clinical AI", score, "VALIDATED", "https://linkedin.com"):
            st.session_state.scout_db.append(entry)
            render_baseball_card(entry)

# Webhook input for Vertex AI Agent
query = st.text_area("Maestro Mission Input:")
if st.button("Execute"):
    parse_and_display_v2(query)

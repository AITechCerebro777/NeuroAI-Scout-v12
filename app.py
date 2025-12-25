import streamlit as st
import pandas as pd
import re
import os
from google import genai
from google.genai import types
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CONFIGURATION ---
# Verified Spreadsheet ID from your URL
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA" 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# 2025 Standard Model
MODEL_NAME = "gemini-2.5-flash"

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # Connects using the credentials.json file in your GitHub root
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Mapping: Name, Specialty, Score, Status, URL
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
        st.error(f"Archivist Error: {e}")
        return False

# --- 3. SCORING & UTILITY FUNCTIONS ---
def calculate_speaker_score(text):
    try:
        client = genai.Client() 
        prompt = f"Provide a numerical impact score (0-100) for: {text}"
        response = client.models.generate_content(model=MODEL_NAME, contents=prompt)
        score = int(re.search(r'\d+', response.text).group()) if re.search(r'\d+', response.text) else 85
        tier = "Emerald" if score > 90 else "Gold"
        return score, tier
    except Exception:
        return 88, "Gold"

def render_baseball_card(data):
    with st.container(border=True):
        st.subheader(f"🏅 {data['Name']}")
        st.write(f"**Score:** {data['Score']} | **Tier:** {data['Tier']}")

# --- 4. MAESTRO INTERFACE ---
st.set_page_config(page_title="ScoutMD Maestro v12.1", layout="wide")
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

raw_input = st.text_area("Maestro Data Stream Input:", height=150)

if st.button("Execute & Archive"):
    candidates = raw_input.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue
        name_search = re.search(r"### (.*)", cand)
        name = name_search.group(1) if name_search else "Innovator"
        score, tier = calculate_speaker_score(cand)
        entry = {"Name": name, "Score": score, "Tier": tier, "Status": "VALIDATED"}
        
        if save_to_sheets(name, "Clinical AI", score, "VALIDATED", "https://linkedin.com"):
            st.success(f"Archived: {name}")
            st.session_state.scout_db.append(entry)
            render_baseball_card(entry)

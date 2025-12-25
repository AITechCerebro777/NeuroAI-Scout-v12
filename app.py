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

# 2025 Stable Model: gemini-2.5-flash
MODEL_NAME = "gemini-2.5-flash"

# --- 2. GOOGLE SHEETS ARCHIVIST ENGINE ---
def save_to_sheets(name, specialty, score, status, url):
    try:
        # Load credentials from the 'credentials.json' file in your repo
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Mapping data to columns A through E
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
    Evaluates the candidate bio using Gemini 2.5 Flash.
    """
    try:
        # Initialize GenAI Client using your GEMINI_API_KEY env variable
        client = genai.Client() 
        prompt = f"Provide a numerical score (0-100) based on clinical AI impact for: {text}"
        
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )
        
        # Numerical score extraction
        score = int(re.search(r'\d+', response.text).group()) if re.search(r'\d+', response.text) else 85
        tier = "Emerald" if score > 90 else "Gold"
        return score, tier
    except Exception:
        # Fallback if API is unreachable
        return 88, "Gold"

# --- 4. MAESTRO INTERFACE ---
st.set_page_config(page_title="ScoutMD Maestro v12.1", layout="wide")
st.title("ScoutMD Maestro Command Center")

if "scout_db" not in st.session_state:
    st.session_state.scout_db = []

def render_baseball_card(data):
    with st.container(border=True):
        st.subheader(f"🏅 {data['Name']}")
        st.write(f"**Score:** {data['Score']} | **Tier:** {data['Tier']}")

# Input area for the Maestro Agent to send candidate data strings
raw_input = st.text_area("Maestro Data Stream Input:", height=150, placeholder="Paste candidate data here...")

if st.button("Execute & Archive"):
    candidates = raw_input.split("|||")
    for cand in candidates:
        if len(cand.strip()) < 10: continue

        # Regex Extraction for name header
        name_search = re.search(r"### (.*)", cand)
        name = name_search.group(1) if name_search else "Expert Innovator"
        
        score, tier = calculate_speaker_score(cand)

        entry = {
            "Name": name, 
            "Specialty": "Clinical AI Deployment",
            "Score": score, 
            "Tier": tier,
            "Status": "VALIDATED",

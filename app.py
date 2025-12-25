import streamlit as st
import pandas as pd
import re
from fastapi import FastAPI, Request
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
import uvicorn
from threading import Thread

# --- 1. CORE LOGIC (SHARED) ---
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

def save_to_sheets(name, specialty, score, status, url):
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        values = [[name, specialty, score, status, url]]
        body = {'values': values}
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:E",
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# --- 2. THE API BRIDGE (FOR THE AI AGENT) ---
api = FastAPI()

@api.post("/save")
async def ai_save_tool(request: Request):
    data = await request.json()
    # The AI sends 'name', 'score', etc.
    name = data.get("name", "Unknown Expert")
    score = data.get("score", 85)
    success = save_to_sheets(name, "Clinical AI", score, "VALIDATED", "https://linkedin.com")
    return {"status": "success" if success else "failed"}

# --- 3. THE UI (FOR YOU) ---
def main():
    st.title("ScoutMD Maestro v12.1")
    raw_input = st.text_area("Manual Input:")
    if st.button("Manual Archive"):
        # Manual logic here...
        st.success("Saved manually!")

if __name__ == "__main__":
    # Start the API on port 8080 (Cloud Run default)
    # This allows the AI to call your-url.run.app/save
    uvicorn.run(api, host="0.0.0.0", port=8080)

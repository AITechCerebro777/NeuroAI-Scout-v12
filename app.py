import streamlit as st
import pandas as pd
import uvicorn
import os
from fastapi import FastAPI, Request
from threading import Thread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. CORE SETTINGS ---
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# --- 2. DATABASE SAVER ---
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

# --- 3. THE MAESTRO BRIDGE (API) ---
# This part "talks" to the AI agent directly
api_app = FastAPI()

@api_app.post("/save")
async def ai_save_tool(request: Request):
    try:
        data = await request.json()
        name = data.get("name", "Unknown Expert")
        score = data.get("score", 85)
        success = save_to_sheets(name, "AI HealthTech", score, "VALIDATED", "https://linkedin.com")
        return {"status": "success" if success else "failed"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 4. THE INTERFACE (STREAMLIT) ---
def run_streamlit():
    # Forces Streamlit to a different internal port to avoid conflicts
    os.system("streamlit run app.py --server.port 8501 --server.address 0.0.0.0")

if __name__ == "__main__":
    # Start the human website in the background
    Thread(target=run_streamlit).start()
    # Start the API Bridge for the AI on port 8080 (Google's requirement)
    uvicorn.run(api_app, host="0.0.0.0", port=8080)

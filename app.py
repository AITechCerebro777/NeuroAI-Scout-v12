import streamlit as st
import pandas as pd
import uvicorn
import os
from fastapi import FastAPI, Request
from threading import Thread
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials

# --- 1. SETTINGS ---
SPREADSHEET_ID = "1_JNbRsLYfp-cXHm9-Y-6-QTfpzBtNETjIBtAeqw4dAA"
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

# This temporary list holds data from the AI until you click "Save"
if "scout_queue" not in st.session_state:
    st.session_state.scout_queue = []

# --- 2. DATABASE SAVER ---
def save_to_sheets(data_list):
    try:
        creds = Credentials.from_service_account_file('credentials.json', scopes=SCOPES)
        service = build('sheets', 'v4', credentials=creds)
        
        # Prepare all rows for one big save
        values = [[d['name'], "Clinical AI", d['score'], "VALIDATED", "https://linkedin.com"] for d in data_list]
        body = {'values': values}
        
        service.spreadsheets().values().append(
            spreadsheetId=SPREADSHEET_ID, range="Sheet1!A:E",
            valueInputOption="USER_ENTERED", body=body
        ).execute()
        return True
    except Exception as e:
        st.error(f"Error saving to Sheet: {e}")
        return False

# --- 3. THE AI BRIDGE (RECEIVING DATA) ---
api_app = FastAPI()

@api_app.post("/save")
async def ai_receive_data(request: Request):
    try:
        data = await request.json()
        # Data is added to memory but NOT yet saved to the spreadsheet
        st.session_state.scout_queue.append(data)
        return {"status": "received", "message": "Data sent to Command Center for review."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 4. COMMAND CENTER INTERFACE ---
def main():
    st.set_page_config(page_title="ScoutMD Command Center", page_icon="🏅")
    st.title("🏅 ScoutMD Maestro Command Center")
    
    st.subheader("Candidates Awaiting Review")
    if st.session_state.scout_queue:
        df = pd.DataFrame(st.session_state.scout_queue)
        st.table(df) # Shows you what the AI found
        
        if st.button("🚨 SAVE ALL TO SPREADSHEET"):
            if save_to_sheets(st.session_state.scout_queue):
                st.success("Success! All data moved to Speaker_DB.")
                st.session_state.scout_queue = [] # Clears the list after saving
    else:
        st.info("Waiting for data from the Maestro Agent...")

if __name__ == "__main__":
    # Start the API Bridge for the AI
    Thread(target=lambda: uvicorn.run(api_app, host="0.0.0.0", port=8080)).start()
    # Start the website for you
    main()

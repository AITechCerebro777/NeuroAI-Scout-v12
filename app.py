import streamlit as st
import pandas as pd
import uvicorn
import os
import re
from fastapi import FastAPI, Request
from threading import Thread

# --- 1. SESSION MEMORY ---
# This keeps your results visible on the screen during your session
if "scout_history" not in st.session_state:
    st.session_state.scout_history = []

# --- 2. THE AI BRIDGE (RECEIVING DATA) ---
api_app = FastAPI()

@api_app.post("/save")
async def receive_from_maestro(request: Request):
    try:
        data = await request.json()
        # Add the AI's findings to your session memory
        st.session_state.scout_history.append({
            "Name": data.get("name", "Unknown"),
            "Score": data.get("score", 0),
            "Tier": "Emerald" if data.get("score", 0) > 90 else "Gold",
            "Status": "VALIDATED"
        })
        return {"status": "success", "message": "Expert added to review table."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- 3. COMMAND CENTER INTERFACE ---
def main():
    st.set_page_config(page_title="ScoutMD Command Center", layout="wide")
    st.title("🏅 ScoutMD Maestro Command Center")
    
    st.subheader("Current Scouting Results")
    if st.session_state.scout_history:
        # Displays everything the AI has found in a clean table
        df = pd.DataFrame(st.session_state.scout_history)
        st.dataframe(df, use_container_width=True)
        
        st.info("💡 You can now copy these results directly into your Speaker_DB spreadsheet.")
        
        if st.button("Clear Results"):
            st.session_state.scout_history = []
            st.rerun()
    else:
        st.info("Waiting for data from the Maestro Agent... Keep this window open.")

if __name__ == "__main__":
    # Start the API Bridge for the AI
    Thread(target=lambda: uvicorn.run(api_app, host="0.0.0.0", port=8080)).start()
    # Start the interface
    main()

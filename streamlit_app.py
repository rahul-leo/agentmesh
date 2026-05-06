import streamlit as st
import requests
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="AgentMesh Dashboard", page_icon="🤖", layout="wide")

st.title("🤖 AgentMesh Streamlit Dashboard")
st.markdown("---")

API_BASE = "http://127.0.0.1:8000"

def fetch_history():
    try:
        response = requests.get(f"{API_BASE}/api/runs?limit=10")
        if response.status_code == 200:
            return response.json().get("runs", [])
    except:
        st.error("Could not connect to AgentMesh API. Make sure the backend is running.")
    return []

col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("🚀 Recent Runs")
    runs = fetch_history()
    if runs:
        for run in runs:
            with st.expander(f"{run.get('task', {}).get('repository', 'Unknown')} - {run.get('status', 'unknown')}"):
                st.json(run)
    else:
        st.write("No runs found.")

with col2:
    st.subheader("⚙️ System Status")
    st.info("AgentMesh Backend: Connected" if runs else "AgentMesh Backend: Disconnected")
    st.write(f"Current Time: {datetime.now().strftime('%H:%M:%S')}")

if st.button("Refresh Data"):
    st.rerun()

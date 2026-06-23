import os
import streamlit as st
import requests
from dotenv import load_dotenv

load_dotenv()

API_URL = os.getenv("API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY")

# Professional Swiggy Orange branding
st.set_page_config(page_title="Swiggy VoC Engine", layout="wide")

# ── Refresh control ─────────────────────────────────────────────────────────
col1, col2 = st.columns([3, 1])
with col1:
    try:
        lu_resp = requests.get(f"{API_URL}/last-updated", timeout=10)
        last_updated = lu_resp.json().get("last_updated", "Unknown")
        st.caption(f"📅 Data last refreshed: {last_updated}")
    except requests.exceptions.RequestException:
        st.caption("📅 Data last refreshed: Unable to check")

with col2:
    if st.button("🔄 Refresh Data"):
        with st.spinner("Scraping fresh reviews... this takes 1-3 minutes"):
            try:
                refresh_resp = requests.post(
                    f"{API_URL}/refresh",
                    headers={"x-api-key": API_KEY},
                    timeout=300
                )
                result = refresh_resp.json()
                if result.get("success"):
                    st.success(f"Refreshed! Last updated: {result['last_updated']}")
                else:
                    st.error(f"Refresh failed at step '{result.get('step')}': {result.get('error', '')[:200]}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach refresh endpoint: {e}")

st.markdown("---")
st.markdown("""
    <style>
    .main-title {
        color: #FC8019 !important;
        font-size: 65px !important;
        font-weight: 900 !important;
        line-height: 1.1 !important;
        margin-bottom: 5px !important;
        display: block !important;
    }
    .sub-title {
        color: #686b78 !important;
        font-size: 26px !important;
        font-weight: 500 !important;
        margin-top: 0px !important;
        margin-bottom: 40px !important;
        display: block !important;
    }
    .block-container {
        padding-top: 4rem !important;
    }
    </style>
    """, unsafe_allow_html=True)

st.markdown('<span class="main-title">Swiggy Voice of Customer Engine</span>', unsafe_allow_html=True)
st.markdown('<span class="sub-title">AI-Powered Root Cause Analysis & Product Insights</span>', unsafe_allow_html=True)
st.markdown("---")

query = st.text_input("Analyze a complaint (e.g., 'delivery partner behavior' or 'refund issues'):")

if query:
    with st.spinner("Generating PM analysis..."):
        try:
            resp = requests.post(
                f"{API_URL}/analyze",
                json={"query": query, "k": 10},
                headers={"x-api-key": API_KEY},
                timeout=30
            )
            resp.raise_for_status()
            result = resp.json()

            st.markdown("### 📊 AI Analysis")
            st.info(result["answer"])

            with st.expander("View Source Reviews"):
                for src in result["sources"]:
                    st.write(f"**{src['user']}** ({src['score']} stars, {src['date']}): {src['text']}")

        except requests.exceptions.HTTPError as e:
            if resp.status_code == 401:
                st.error("Authentication failed. Check that API_KEY matches the backend's .env.")
            elif resp.status_code == 503:
                st.error("Vector DB not found on the server. Run build_vector_db.py first.")
            else:
                st.error(f"Server error: {e}")
        except requests.exceptions.RequestException as e:
            st.error(f"Could not reach analysis service at {API_URL}: {e}")
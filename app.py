import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="ClimateTwin Control Center", layout="wide")

st.title("🌍 ClimateTwin: Master Dashboard")
st.markdown("Welcome to the **ClimateTwin Control Center**. This dashboard visualizes the results of the comprehensive 16-domain evaluation suite.")

results_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\results"
benchmark_dir = r"C:\Users\gokul\Desktop\PROJECTS\climatetwin\benchmark"

tab1, tab2, tab3, tab4, tab5 = st.tabs(["Benchmark Leaderboard", "Decision Optimization (DCA)", "GIS Topology Constraints", "Cybersecurity Harness", "Alert Flapping (Hysteresis)"])

with tab1:
    st.header("🏆 Model Benchmark Leaderboard")
    st.markdown("Strict isolation between REAL observations and SYNTHETIC cascade topologies to prevent metric inflation.")
    try:
        df_leaderboard = pd.read_csv(os.path.join(benchmark_dir, "leaderboard.csv"))
        st.dataframe(df_leaderboard, use_container_width=True)
    except Exception as e:
        st.warning(f"Leaderboard data not found: {e}")

with tab2:
    st.header("📊 Decision Curve Analysis (Expected Utility)")
    st.markdown("Optimization of probability thresholds against simulated asymmetric financial damage costs (Missed Flood vs False Alarm).")
    try:
        df_dca = pd.read_csv(os.path.join(results_dir, "decision_dca.csv"))
        st.line_chart(df_dca.set_index("Threshold")["Expected_Cost"], color="#FF4B4B")
        st.dataframe(df_dca, use_container_width=True)
    except:
        st.warning("DCA data not found.")

with tab3:
    st.header("🗺️ Physical GIS Topology vs Synthetic Illusion")
    st.markdown("Performance drops significantly when moving from a perfectly-mapped synthetic graph to a real incomplete GIS topology.")
    try:
        df_gnn = pd.read_csv(os.path.join(results_dir, "physical_gnn_lstm_metrics.csv"))
        st.bar_chart(df_gnn.set_index("Model")["Impact_F1"])
        st.dataframe(df_gnn, use_container_width=True)
    except:
        st.warning("GIS data not found.")

with tab4:
    st.header("🛡️ Local Cybersecurity Harness")
    st.markdown("Validating the defensive HMAC/Nonce/Plausibility pipeline against hostile simulated ingestion streams.")
    try:
        df_cyber = pd.read_csv(os.path.join(results_dir, "cybersecurity_metrics.csv"))
        st.dataframe(df_cyber.style.highlight_max(axis=0), use_container_width=True)
    except:
        st.warning("Cybersecurity data not found.")

with tab5:
    st.header("🛑 Alert Fatigue & Hysteresis")
    st.markdown("Comparing a naive raw-probability threshold vs a stateful controller with cooldowns to eradicate UI flapping.")
    try:
        df_hyst = pd.read_csv(os.path.join(results_dir, "alert_hysteresis.csv"))
        st.bar_chart(df_hyst.set_index("Policy")["Flapping_Count"], color="#00C0F2")
        st.dataframe(df_hyst, use_container_width=True)
    except:
        st.warning("Hysteresis data not found.")

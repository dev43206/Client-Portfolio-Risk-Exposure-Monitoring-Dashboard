"""Streamlit UI for the independent client exposure dashboard section."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from .calculations import calculate_available_credit, generate_client_exposure_summary
from .data import load_sample_data
from database.queries import get_exposure_history, save_exposure_snapshot


def render_client_exposure() -> None:
    """Render client selector, exposure summary, KPIs, positions, and comparison."""
    st.header("Client Exposure Monitoring")
    st.caption("Educational monitoring based on supplied position market values.")
    try:
        clients, positions = load_sample_data()
    except Exception:
        st.error("Client exposure data is unavailable. Check the local database setup and try again.")
        return
    if clients.empty:
        st.info("No client data is available. Initialize the database with `python -m database.seed`.")
        return
    summary = generate_client_exposure_summary(clients, positions)
    client_id = st.selectbox("Select client", summary["client_id"].tolist(), format_func=lambda value: summary.loc[summary["client_id"] == value, "client_name"].iloc[0])
    selected = summary.loc[summary["client_id"] == client_id].iloc[0]
    client_name = selected["client_name"]
    client_positions = positions.loc[positions["client_id"] == selected["client_id"]].copy()
    cols = st.columns(4)
    cols[0].metric("Credit Limit", f"${selected['credit_limit']:,.2f}")
    cols[1].metric("Current Exposure", f"${selected['exposure']:,.2f}")
    cols[2].metric("Available Credit", f"${calculate_available_credit(selected['credit_limit'], selected['exposure']):,.2f}")
    cols[3].metric("Utilization", f"{selected['utilization']:.1f}%")
    st.subheader(f"Risk Status: {selected['risk_status']}")
    st.caption(f"Risk profile: {selected['risk_profile']} (client classification, not a prediction).")

    st.subheader("Client Exposure Summary")
    display = summary[["client_name", "credit_limit", "exposure", "utilization", "risk_status"]].rename(
        columns={"client_name": "Client", "credit_limit": "Credit Limit", "exposure": "Exposure", "utilization": "Utilization %", "risk_status": "Risk Status"}
    )
    st.dataframe(display.style.format({"Credit Limit": "${:,.2f}", "Exposure": "${:,.2f}", "Utilization %": "{:.1f}%"}), use_container_width=True, hide_index=True)

    st.subheader("Portfolio Positions")
    st.dataframe(client_positions[["instrument", "quantity", "price", "market_value"]].rename(columns={"instrument": "Instrument", "quantity": "Quantity", "price": "Price", "market_value": "Market Value"}).style.format({"Price": "${:,.2f}", "Market Value": "${:,.2f}"}), use_container_width=True, hide_index=True)

    st.subheader("Credit Limit vs Current Exposure")
    fig = go.Figure(data=[
        go.Bar(name="Credit Limit", x=[client_name], y=[selected["credit_limit"]]),
        go.Bar(name="Current Exposure", x=[client_name], y=[selected["exposure"]]),
    ])
    fig.update_layout(barmode="group", yaxis_title="Amount ($)")
    st.plotly_chart(fig, use_container_width=True)
    if st.button("Save Risk Snapshot"):
        try:
            save_exposure_snapshot(
                int(selected["client_id"]), float(selected["exposure"]),
                float(selected["credit_limit"]), float(selected["utilization"]),
                str(selected["risk_status"]),
            )
            st.success("Risk snapshot saved.")
        except Exception:
            st.error("The risk snapshot could not be saved. Check the database and selected client.")
    st.subheader("Exposure History")
    try:
        history = pd.DataFrame(get_exposure_history(int(selected["client_id"])))
        if history.empty:
            st.info("No saved snapshots for this client yet.")
        else:
            st.dataframe(history[["snapshot_date", "current_exposure", "credit_limit", "utilization", "risk_status"]], use_container_width=True, hide_index=True)
    except Exception:
        st.error("Exposure history is unavailable.")
    st.caption("Current exposure = max(total portfolio market value, 0). Risk bands are simplified educational thresholds: <50% LOW, 50–<80% MEDIUM, 80–<100% HIGH, ≥100% BREACH.")

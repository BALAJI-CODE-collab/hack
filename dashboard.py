#!/usr/bin/env python
"""Streamlit Dashboard for Poaching Data Analysis"""
import streamlit as st
import sqlite3
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from pathlib import Path

# Page configuration
st.set_page_config(
    page_title="Poaching Risk Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.markdown("""
    <div style='text-align: center; padding: 20px;'>
        <h1>🌍 Global Wildlife Protection Dashboard</h1>
        <h3>Poaching Risk Analysis & Hotspot Detection</h3>
    </div>
    """, unsafe_allow_html=True)

def query_to_df(query, params=()):
    conn = sqlite3.connect('poaching_dashboard.db')
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df

# ===== SIDEBAR =====
st.sidebar.markdown("### 📊 Dashboard Filters")

selected_region = st.sidebar.selectbox(
    "Select Region",
    ["All Regions", "Serengeti National Park", "Amazon Rainforest", "Southeast Asia Mangroves", "Congo Basin"]
)

date_range = st.sidebar.date_input(
    "Select Date Range",
    value=(datetime.now() - timedelta(days=30), datetime.now()),
    max_value=datetime.now()
)

risk_level_filter = st.sidebar.multiselect(
    "Filter by Risk Level",
    ["Very High", "High", "Medium", "Low"],
    default=["Very High", "High"]
)

# ===== MAIN DASHBOARD =====

# Get region ID
region_map = {
    "Serengeti National Park": 1,
    "Amazon Rainforest": 2,
    "Southeast Asia Mangroves": 3,
    "Congo Basin": 4
}

region_id = None if selected_region == "All Regions" else region_map[selected_region]

# ===== ROW 1: KEY METRICS =====
col1, col2, col3, col4 = st.columns(4)

# Total Incidents
query = 'SELECT COUNT(*) as count FROM poaching_incidents WHERE incident_date BETWEEN ? AND ?'
if region_id:
    query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'
total_incidents = query_to_df(query, (date_range[0], date_range[1]))['count'][0]

col1.metric("🚨 Total Incidents", total_incidents, delta="+5 this week")

# Average Risk
query = 'SELECT AVG(risk_probability) as avg_risk FROM risk_predictions WHERE prediction_date BETWEEN ? AND ?'
if region_id:
    query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'
avg_risk = query_to_df(query, (date_range[0], date_range[1]))['avg_risk'][0]
col2.metric("📈 Avg Risk Score", f"{avg_risk:.2%}" if avg_risk else "N/A")

# High Risk Areas
query = 'SELECT COUNT(*) as count FROM risk_predictions WHERE risk_level IN ("High", "Very High") AND prediction_date BETWEEN ? AND ?'
if region_id:
    query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'
high_risk_areas = query_to_df(query, (date_range[0], date_range[1]))['count'][0]
col3.metric("🔴 High Risk Areas", high_risk_areas)

# Monitored Grid Cells
query = 'SELECT COUNT(DISTINCT grid_id) as count FROM grid_cells'
if region_id:
    query += f' WHERE region_id = {region_id}'
monitored_cells = query_to_df(query)['count'][0]
col4.metric("📍 Monitored Cells", monitored_cells)

st.divider()

# ===== ROW 2: CHARTS =====
col1, col2 = st.columns(2)

# Incidents by Region
with col1:
    st.subheader("📊 Incidents by Region")
    query = '''
        SELECT r.region_name, COUNT(pi.incident_id) as incidents
        FROM regions r
        LEFT JOIN grid_cells gc ON r.region_id = gc.region_id
        LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
        WHERE pi.incident_date BETWEEN ? AND ?
        GROUP BY r.region_id, r.region_name
        ORDER BY incidents DESC
    '''
    region_incidents = query_to_df(query, (date_range[0], date_range[1]))
    
    if not region_incidents.empty:
        fig = px.bar(
            region_incidents,
            x='region_name',
            y='incidents',
            color='incidents',
            color_continuous_scale='Reds',
            labels={'region_name': 'Region', 'incidents': 'Incidents'}
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No incidents in selected period")

# Risk Level Distribution
with col2:
    st.subheader("🎯 Risk Level Distribution")
    query = '''
        SELECT risk_level, COUNT(*) as count
        FROM risk_predictions
        WHERE prediction_date BETWEEN ? AND ?
    '''
    if region_id:
        query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'
    query += ' GROUP BY risk_level'
    
    risk_dist = query_to_df(query, (date_range[0], date_range[1]))
    
    if not risk_dist.empty:
        color_map = {'Very High': '#d73027', 'High': '#fc8d59', 'Medium': '#fee090', 'Low': '#e0f2f7'}
        fig = px.pie(
            risk_dist,
            names='risk_level',
            values='count',
            color='risk_level',
            color_discrete_map=color_map
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No risk data available")

st.divider()

# ===== ROW 3: HOTSPOT ANALYSIS =====
st.subheader("🔥 Poaching Hotspots (Where It Happens Most)")

query = '''
    SELECT 
        gc.grid_id,
        r.region_name,
        gc.latitude,
        gc.longitude,
        COUNT(pi.incident_id) as incident_count,
        AVG(rp.risk_probability) as avg_risk,
        rp.risk_level
    FROM grid_cells gc
    LEFT JOIN regions r ON gc.region_id = r.region_id
    LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
    LEFT JOIN risk_predictions rp ON gc.grid_id = rp.grid_id
    WHERE pi.incident_date BETWEEN ? AND ?
'''

if region_id:
    query += f' AND gc.region_id = {region_id}'

query += ' GROUP BY gc.grid_id ORDER BY incident_count DESC LIMIT 15'

hotspots = query_to_df(query, (date_range[0], date_range[1]))

if not hotspots.empty:
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.write("**Top 15 Hotspot Grid Cells:**")
        hotspots_display = hotspots[['grid_id', 'region_name', 'incident_count', 'avg_risk', 'risk_level']].copy()
        hotspots_display['avg_risk'] = hotspots_display['avg_risk'].apply(lambda x: f"{x:.2%}" if pd.notna(x) else "N/A")
        hotspots_display.columns = ['Grid ID', 'Region', 'Incidents', 'Avg Risk', 'Risk Level']
        st.dataframe(hotspots_display, use_container_width=True)
    
    with col2:
        st.write("**Incidents by Grid:**")
        fig = px.bar(
            hotspots.head(10),
            x='incident_count',
            y='grid_id',
            orientation='h',
            color='incident_count',
            color_continuous_scale='Reds',
            labels={'incident_count': 'Incident Count', 'grid_id': 'Grid'}
        )
        st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No hotspot data available for selected filters")

st.divider()

# ===== ROW 4: ANIMAL-SPECIFIC ANALYSIS =====
st.subheader("🦁 Endangered Animals & Poaching Incidents")

query = '''
    SELECT animal_type, COUNT(*) as incident_count, severity
    FROM poaching_incidents
    WHERE incident_date BETWEEN ? AND ?
'''

if region_id:
    query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'

query += ' GROUP BY animal_type ORDER BY incident_count DESC'

animal_stats = query_to_df(query, (date_range[0], date_range[1]))

if not animal_stats.empty:
    col1, col2 = st.columns(2)
    
    with col1:
        fig = px.bar(
            animal_stats,
            x='animal_type',
            y='incident_count',
            color='incident_count',
            color_continuous_scale='Reds',
            labels={'animal_type': 'Animal Type', 'incident_count': 'Incidents'}
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.write("**Incident Summary by Animal:**")
        animal_summary = animal_stats[['animal_type', 'incident_count']].copy()
        animal_summary.columns = ['Animal', 'Incidents']
        st.dataframe(animal_summary, use_container_width=True)
else:
    st.info("No animal incident data available")

st.divider()

# ===== ROW 5: TIMELINE ANALYSIS =====
st.subheader("📅 Incident Timeline")

query = '''
    SELECT DATE(incident_date) as date, COUNT(*) as incidents
    FROM poaching_incidents
    WHERE incident_date BETWEEN ? AND ?
'''

if region_id:
    query += f' AND grid_id IN (SELECT grid_id FROM grid_cells WHERE region_id = {region_id})'

query += ' GROUP BY DATE(incident_date) ORDER BY date'

timeline = query_to_df(query, (date_range[0], date_range[1]))

if not timeline.empty:
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline['date'],
        y=timeline['incidents'],
        mode='lines+markers',
        fill='tozeroy',
        name='Incidents',
        line=dict(color='#d73027', width=3),
        marker=dict(size=8)
    ))
    fig.update_layout(
        title='Daily Poaching Incidents Over Time',
        xaxis_title='Date',
        yaxis_title='Incidents',
        hovermode='x unified',
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No timeline data available")

st.divider()

# ===== FOOTER =====
st.markdown("""
    ---
    <div style='text-align: center; color: #888;'>
        <p>🌍 Global Wildlife Protection Dashboard | Data Updated: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
        <p>Using SQLite Database | Real-time Risk Analysis | Hotspot Detection</p>
    </div>
    """, unsafe_allow_html=True)

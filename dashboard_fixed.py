import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta

st.set_page_config(page_title="Poaching Risk Dashboard", page_icon="🛡️", layout="wide")

st.markdown("<h1 style='text-align: center;'>🌍 Wildlife Protection Dashboard</h1>", unsafe_allow_html=True)
st.markdown("<h3 style='text-align: center;'>Poaching Hotspot Analysis</h3>", unsafe_allow_html=True)
st.divider()

def get_query(query_str, params=()):
    conn = sqlite3.connect('poaching_dashboard.db')
    df = pd.read_sql_query(query_str, conn, params=params)
    conn.close()
    return df

st.sidebar.title("📊 Filters")
selected_region = st.sidebar.selectbox("Region", ["All Regions", "Serengeti National Park", "Amazon Rainforest", "Southeast Asia Mangroves", "Congo Basin"])
days_back = st.sidebar.slider("Last N days", 7, 365, 30)

region_map = {"Serengeti National Park": 1, "Amazon Rainforest": 2, "Southeast Asia Mangroves": 3, "Congo Basin": 4}
region_id = region_map.get(selected_region)

col1, col2, col3, col4 = st.columns(4)

try:
    start_date = (datetime.now() - timedelta(days=days_back)).date()
    
    if region_id:
        total_q = f"SELECT COUNT(*) as count FROM poaching_incidents pi JOIN grid_cells gc ON pi.grid_id = gc.grid_id WHERE gc.region_id = {region_id} AND pi.incident_date >= '{start_date}'"
    else:
        total_q = f"SELECT COUNT(*) as count FROM poaching_incidents WHERE incident_date >= '{start_date}'"
    
    total = get_query(total_q)
    col1.metric("🚨 Total Incidents", int(total['count'][0]) if len(total) > 0 else 0)
    
    if region_id:
        avg_q = f"SELECT AVG(risk_probability) as avg_risk FROM risk_predictions rp JOIN grid_cells gc ON rp.grid_id = gc.grid_id WHERE gc.region_id = {region_id}"
    else:
        avg_q = "SELECT AVG(risk_probability) as avg_risk FROM risk_predictions"
    
    avg_risk = get_query(avg_q)
    avg_val = avg_risk['avg_risk'][0] if len(avg_risk) > 0 and avg_risk['avg_risk'][0] else 0
    col2.metric("📈 Avg Risk", f"{avg_val:.1%}")
    
    if region_id:
        high_q = f"SELECT COUNT(*) as count FROM risk_predictions rp JOIN grid_cells gc ON rp.grid_id = gc.grid_id WHERE gc.region_id = {region_id} AND rp.risk_level IN ('High', 'Very High')"
    else:
        high_q = "SELECT COUNT(*) as count FROM risk_predictions WHERE risk_level IN ('High', 'Very High')"
    
    high_risk = get_query(high_q)
    col3.metric("🔴 High Risk Areas", int(high_risk['count'][0]) if len(high_risk) > 0 else 0)
    
    cells_q = "SELECT COUNT(DISTINCT grid_id) as count FROM grid_cells" if not region_id else f"SELECT COUNT(DISTINCT grid_id) as count FROM grid_cells WHERE region_id = {region_id}"
    cells = get_query(cells_q)
    col4.metric("📍 Monitored", int(cells['count'][0]) if len(cells) > 0 else 0)
    
except Exception as e:
    st.error(f"Error loading metrics: {e}")

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Incidents by Region")
    try:
        reg_q = """SELECT r.region_name, COUNT(pi.incident_id) as incidents
        FROM regions r
        LEFT JOIN grid_cells gc ON r.region_id = gc.region_id
        LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
        GROUP BY r.region_id, r.region_name
        ORDER BY incidents DESC"""
        
        if region_id:
            reg_q = f"""SELECT r.region_name, COUNT(pi.incident_id) as incidents
            FROM regions r
            LEFT JOIN grid_cells gc ON r.region_id = gc.region_id
            LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
            WHERE r.region_id = {region_id}
            GROUP BY r.region_id"""
        
        reg_data = get_query(reg_q)
        if len(reg_data) > 0:
            fig = px.bar(reg_data, x='region_name', y='incidents', color='incidents', color_continuous_scale='Reds')
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

with col2:
    st.subheader("🎯 Risk Distribution")
    try:
        risk_q = "SELECT risk_level, COUNT(*) as count FROM risk_predictions GROUP BY risk_level"
        if region_id:
            risk_q = f"SELECT rp.risk_level, COUNT(*) as count FROM risk_predictions rp JOIN grid_cells gc ON rp.grid_id = gc.grid_id WHERE gc.region_id = {region_id} GROUP BY rp.risk_level"
        
        risk_data = get_query(risk_q)
        if len(risk_data) > 0:
            color_map = {'Very High': '#d73027', 'High': '#fc8d59', 'Medium': '#fee090', 'Low': '#e0f2f7'}
            fig = px.pie(risk_data, names='risk_level', values='count', color='risk_level', color_discrete_map=color_map)
            st.plotly_chart(fig, use_container_width=True)
    except Exception as e:
        st.error(f"Error: {e}")

st.divider()

st.subheader("🔥 TOP POACHING HOTSPOTS (Where to Patrol)")

try:
    hotspot_q = """SELECT gc.grid_id, r.region_name, gc.latitude, gc.longitude, 
    COUNT(pi.incident_id) as incidents, AVG(rp.risk_probability) as avg_risk, rp.risk_level
    FROM grid_cells gc
    LEFT JOIN regions r ON gc.region_id = r.region_id
    LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
    LEFT JOIN risk_predictions rp ON gc.grid_id = rp.grid_id
    GROUP BY gc.grid_id
    ORDER BY incidents DESC, avg_risk DESC
    LIMIT 15"""
    
    if region_id:
        hotspot_q = f"""SELECT gc.grid_id, r.region_name, gc.latitude, gc.longitude, 
        COUNT(pi.incident_id) as incidents, AVG(rp.risk_probability) as avg_risk, rp.risk_level
        FROM grid_cells gc
        LEFT JOIN regions r ON gc.region_id = r.region_id
        LEFT JOIN poaching_incidents pi ON gc.grid_id = pi.grid_id
        LEFT JOIN risk_predictions rp ON gc.grid_id = rp.grid_id
        WHERE gc.region_id = {region_id}
        GROUP BY gc.grid_id
        ORDER BY incidents DESC, avg_risk DESC
        LIMIT 15"""
    
    hotspots = get_query(hotspot_q)
    
    if len(hotspots) > 0:
        hotspots['avg_risk'] = hotspots['avg_risk'].apply(lambda x: f"{x:.1%}" if pd.notna(x) else "N/A")
        hotspots['incidents'] = hotspots['incidents'].fillna(0).astype(int)
        
        display_cols = ['grid_id', 'region_name', 'latitude', 'longitude', 'incidents', 'avg_risk', 'risk_level']
        hotspots_display = hotspots[display_cols].copy()
        hotspots_display.columns = ['Grid ID', 'Region', 'Lat', 'Lon', 'Incidents', 'Risk%', 'Level']
        
        st.dataframe(hotspots_display, use_container_width=True)
        
        st.info("👆 Use these coordinates to deploy ranger patrols - highest incident areas first!")
    else:
        st.info("No hotspot data available")
        
except Exception as e:
    st.error(f"Error loading hotspots: {e}")

st.divider()

st.subheader("🦁 Animal-Specific Incidents")

try:
    animal_q = "SELECT animal_type, COUNT(*) as incidents FROM poaching_incidents WHERE animal_type IS NOT NULL GROUP BY animal_type ORDER BY incidents DESC"
    
    if region_id:
        animal_q = f"SELECT pi.animal_type, COUNT(*) as incidents FROM poaching_incidents pi JOIN grid_cells gc ON pi.grid_id = gc.grid_id WHERE gc.region_id = {region_id} AND pi.animal_type IS NOT NULL GROUP BY pi.animal_type ORDER BY incidents DESC"
    
    animals = get_query(animal_q)
    
    if len(animals) > 0:
        col1, col2 = st.columns(2)
        with col1:
            fig = px.bar(animals, x='animal_type', y='incidents', color='incidents', color_continuous_scale='Reds')
            fig.update_layout(showlegend=False)
            st.plotly_chart(fig, use_container_width=True)
        with col2:
            st.dataframe(animals[['animal_type', 'incidents']], use_container_width=True)
    else:
        st.info("No animal incident data")
        
except Exception as e:
    st.error(f"Error: {e}")

st.divider()

st.markdown("<p style='text-align: center; color: #888;'>🌍 Global Wildlife Protection Dashboard | Last Updated: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + "</p>", unsafe_allow_html=True)

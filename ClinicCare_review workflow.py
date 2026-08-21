import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="National Grid Dashboard", layout="wide")
st.title("National Electricity Grid — Analytics Dashboard")

substations = pd.read_csv('substations.csv')
lines = pd.read_csv('lines.csv')
n1_results = pd.read_csv('n1_contingency_results.csv')

tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Network", "Geography", "Reliability"])

with tab1:
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Substations", len(substations))
    col2.metric("Total Lines", len(lines))
    col3.metric("Regions Covered", substations['Region'].nunique())
    st.dataframe(substations.head(10))

with tab2:
    st.subheader("N-1 Contingency Results")
    st.dataframe(n1_results)
    region_filter = st.selectbox("Filter substations by region", ["All"] + sorted(substations['Region'].unique().tolist()))
    filtered = substations if region_filter == "All" else substations[substations['Region'] == region_filter]
    st.dataframe(filtered)

with tab3:
    fig = px.scatter_geo(substations, lat='Latitude', lon='Longitude', hover_name='Name',
                          color='Region', title='Substation Locations', projection='natural earth')
    st.plotly_chart(fig, use_container_width=True)

with tab4:
    fig2 = px.bar(lines['Status'].value_counts().reset_index(),
                   x='Status', y='count', title='Line Status Distribution')
    st.plotly_chart(fig2, use_container_width=True)

st.sidebar.header("Search")
search_term = st.sidebar.text_input("Search for a substation")
if search_term:
    results = substations[substations['Name'].str.contains(search_term, case=False, na=False)]
    st.sidebar.dataframe(results)
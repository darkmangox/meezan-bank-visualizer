import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="Meezan Bank Visualizer", layout="wide")
st.title("🏦 Meezan Bank Statement Visualizer")
st.markdown("Upload your Meezan Bank CSV file to visualize your transactions")

uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file is not None:
    try:
        df = pd.read_csv(uploaded_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        st.success(f"✅ Loaded {len(df)} transactions")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Transactions", len(df))
        with col2:
            income = df[df['Amount'] > 0]['Amount'].sum()
            st.metric("Income", f"₹{income:,.2f}")
        with col3:
            expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
            st.metric("Expenses", f"₹{expenses:,.2f}")
        with col4:
            net = df['Amount'].sum()
            st.metric("Net Flow", f"₹{net:,.2f}")
        
        # Balance chart
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')
        df_sorted['Running Balance'] = df_sorted['Amount'].cumsum()
        fig = px.line(df_sorted, x='Date', y='Running Balance')
        st.plotly_chart(fig, use_container_width=True)
        
        # Transactions table
        st.subheader("📋 Transaction History")
        st.dataframe(df.sort_values('Date', ascending=False))
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
else:
    st.info("👆 Upload your Meezan Bank CSV file to begin")
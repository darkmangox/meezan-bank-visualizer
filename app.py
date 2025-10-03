import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(page_title="Meezan Bank Visualizer", layout="wide")
st.title("🏦 Meezan Bank Statement Visualizer")
st.markdown("Upload your Meezan Bank CSV file to visualize your transactions")

# File upload
uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read data
        df = pd.read_csv(uploaded_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        st.success(f"✅ Successfully loaded {len(df)} transactions")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            total_income = df[df['Amount'] > 0]['Amount'].sum()
            st.metric("Total Income", f"₹{total_income:,.2f}")
        
        with col3:
            total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
            st.metric("Total Expenses", f"₹{total_expenses:,.2f}")
        
        with col4:
            net_flow = df['Amount'].sum()
            st.metric("Net Flow", f"₹{net_flow:,.2f}")
        
        # Balance over time chart - USING ACTUAL BALANCES
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')
        
        # Check if Available Balance column exists
        if 'Available Balance' in df.columns:
            # Use the actual Available Balance from your bank statement
            fig = px.line(df_sorted, x='Date', y='Available Balance', 
                         title='Actual Account Balance Over Time (From Bank Records)')
            fig.update_layout(yaxis_title="Balance (₹)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show current balance
            current_balance = df_sorted['Available Balance'].iloc[-1]
            st.metric("Current Balance", f"₹{current_balance:,.2f}")
        else:
            # Fallback to calculated balance
            df_sorted['Running Balance'] = df_sorted['Amount'].cumsum()
            fig = px.line(df_sorted, x='Date', y='Running Balance', 
                         title='Calculated Balance Over Time')
            st.plotly_chart(fig, use_container_width=True)
            st.info("Using calculated balance (no Available Balance column found)")
        
        # Monthly summary
        st.subheader("📊 Monthly Summary")
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        monthly_data = df.groupby('Month').agg({
            'Amount': ['sum', 'count']
        }).round(2)
        monthly_data.columns = ['Net Amount', 'Transaction Count']
        st.dataframe(monthly_data, use_container_width=True)
        
        # Income vs Expenses pie chart
        st.subheader("🍕 Income vs Expenses")
        income = df[df['Amount'] > 0]['Amount'].sum()
        expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
        
        if income + expenses > 0:  # Only show if we have data
            fig2 = px.pie(values=[income, expenses], 
                         names=['Income', 'Expenses'],
                         title='Income vs Expenses Distribution')
            st.plotly_chart(fig2, use_container_width=True)
        
        # Transaction history
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.sort_values('Date', ascending=False).head(100))
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

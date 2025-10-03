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
        
        # Monthly Expenditure Bar Graph
        st.subheader("📊 Monthly Expenditure")
        
        # Create month-year column
        df['Month_Year'] = df['Date'].dt.strftime('%Y-%m')
        
        # Calculate monthly expenses (only negative amounts)
        monthly_expenses = df[df['Amount'] < 0].groupby('Month_Year').agg({
            'Amount': 'sum'
        }).reset_index()
        
        # Convert to positive values for the chart
        monthly_expenses['Expenditure'] = abs(monthly_expenses['Amount'])
        monthly_expenses = monthly_expenses.sort_values('Month_Year')
        
        if not monthly_expenses.empty:
            fig_expenses = px.bar(monthly_expenses, 
                                x='Month_Year', 
                                y='Expenditure',
                                title='Monthly Expenditure (₹)',
                                color='Expenditure',
                                color_continuous_scale='reds')
            
            fig_expenses.update_layout(xaxis_title="Month", 
                                     yaxis_title="Expenditure (₹)",
                                     xaxis={'tickangle': 45})
            st.plotly_chart(fig_expenses, use_container_width=True)
            
            # Show monthly expenditure summary
            st.subheader("💸 Monthly Expenditure Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_monthly_expense = monthly_expenses['Expenditure'].mean()
                st.metric("Average Monthly Spend", f"₹{avg_monthly_expense:,.2f}")
            
            with col2:
                max_monthly_expense = monthly_expenses['Expenditure'].max()
                max_month = monthly_expenses.loc[monthly_expenses['Expenditure'].idxmax(), 'Month_Year']
                st.metric("Highest Spending Month", f"₹{max_monthly_expense:,.2f}", f"({max_month})")
            
            with col3:
                min_monthly_expense = monthly_expenses['Expenditure'].min()
                min_month = monthly_expenses.loc[monthly_expenses['Expenditure'].idxmin(), 'Month_Year']
                st.metric("Lowest Spending Month", f"₹{min_monthly_expense:,.2f}", f"({min_month})")
        else:
            st.info("No expenditure data found for the selected period")
        
        # Monthly summary (income vs expenses)
        st.subheader("📈 Monthly Income vs Expenses")
        
        monthly_summary = df.groupby('Month_Year').agg({
            'Amount': lambda x: x[x > 0].sum(),  # Income
            'Amount': lambda x: abs(x[x < 0].sum())  # Expenses
        }).reset_index()
        
        monthly_summary.columns = ['Month_Year', 'Income', 'Expenses']
        monthly_summary = monthly_summary.sort_values('Month_Year')
        
        if not monthly_summary.empty:
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(name='Income', 
                                          x=monthly_summary['Month_Year'], 
                                          y=monthly_summary['Income'],
                                          marker_color='green'))
            fig_comparison.add_trace(go.Bar(name='Expenses', 
                                          x=monthly_summary['Month_Year'], 
                                          y=monthly_summary['Expenses'],
                                          marker_color='red'))
            fig_comparison.update_layout(barmode='group',
                                       title='Monthly Income vs Expenses',
                                       xaxis_title="Month",
                                       yaxis_title="Amount (₹)",
                                       xaxis={'tickangle': 45})
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Transaction history
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.sort_values('Date', ascending=False).head(100))
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re

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
        
        # Auto-detect and mark transfers to Daniyal and Talha Ahmed as non-transactions
        names_to_exclude = ['Daniyal', 'Talha Ahmed']
        transfer_pattern = '|'.join([f'to {name}' for name in names_to_exclude])
        df['Is_Transfer_Not_Transaction'] = df['Description'].str.contains(transfer_pattern, case=False, na=False)
        
        # Create filtered dataframe that excludes these transfers
        df_filtered = df[~df['Is_Transfer_Not_Transaction']].copy()
        
        st.success(f"✅ Successfully loaded {len(df_filtered)} real transactions")
        st.info(f"📤 Excluded {len(df) - len(df_filtered)} transfers to Daniyal/Talha Ahmed")
        
        # Display summary metrics (using FILTERED data)
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Real Transactions", len(df_filtered))
        
        with col2:
            real_income = df_filtered[df_filtered['Amount'] > 0]['Amount'].sum()
            st.metric("Real Income", f"Rs. {real_income:,.2f}")
        
        with col3:
            real_expenses = abs(df_filtered[df_filtered['Amount'] < 0]['Amount'].sum())
            st.metric("Real Expenses", f"Rs. {real_expenses:,.2f}")
        
        with col4:
            real_net_flow = df_filtered['Amount'].sum()
            st.metric("Real Net Flow", f"Rs. {real_net_flow:,.2f}")
        
        # Balance over time chart - USING ACTUAL BALANCES (from original data for accuracy)
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')  # Use original data for balance accuracy
        
        # Check if Available Balance column exists
        if 'Available Balance' in df.columns:
            # Use the actual Available Balance from your bank statement
            fig = px.line(df_sorted, x='Date', y='Available Balance', 
                         title='Actual Account Balance Over Time (From Bank Records)')
            fig.update_layout(yaxis_title="Balance (Rs.)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show current balance
            current_balance = df_sorted['Available Balance'].iloc[-1]
            st.metric("Current Balance", f"Rs. {current_balance:,.2f}")
        else:
            # Fallback to calculated balance
            df_sorted['Running Balance'] = df_sorted['Amount'].cumsum()
            fig = px.line(df_sorted, x='Date', y='Running Balance', 
                         title='Calculated Balance Over Time')
            st.plotly_chart(fig, use_container_width=True)
            st.info("Using calculated balance (no Available Balance column found)")

        # Yearly Upwork Income Chart (Net after subtracting Daniyal/Talha transfers)
        st.subheader("💼 Yearly Upwork Income (Net)")
        
        # Create year column
        df['Year'] = df['Date'].dt.strftime('%Y')
        df_filtered['Year'] = df_filtered['Date'].dt.strftime('%Y')
        
        # Calculate yearly Upwork income (from filtered data - already excludes transfers)
        upwork_income = df_filtered[
            (df_filtered['Amount'] > 0) & 
            (df_filtered['Description'].str.contains('upwork', case=False, na=False))
        ].groupby('Year').agg({
            'Amount': 'sum',
            'Description': 'count'
        }).reset_index()
        
        upwork_income = upwork_income.rename(columns={
            'Amount': 'Upwork_Income',
            'Description': 'Transaction_Count'
        })
        
        # Calculate total transfers to Daniyal/Talha per year (to show the deduction)
        yearly_transfers = df[df['Is_Transfer_Not_Transaction']].groupby('Year').agg({
            'Amount': 'sum'
        }).reset_index()
        yearly_transfers['Transfer_Amount'] = abs(yearly_transfers['Amount'])
        
        # Merge to create net income calculation
        yearly_income_breakdown = pd.merge(
            upwork_income, 
            yearly_transfers[['Year', 'Transfer_Amount']], 
            on='Year', 
            how='left'
        ).fillna(0)
        
        # Calculate net Upwork income (after subtracting transfers)
        yearly_income_breakdown['Net_Upwork_Income'] = (
            yearly_income_breakdown['Upwork_Income'] - yearly_income_breakdown['Transfer_Amount']
        )
        
        if not yearly_income_breakdown.empty:
            # Create stacked bar chart showing gross vs net
            fig_upwork = go.Figure()
            
            # Gross Upwork income
            fig_upwork.add_trace(go.Bar(
                name='Gross Upwork Income',
                x=yearly_income_breakdown['Year'],
                y=yearly_income_breakdown['Upwork_Income'],
                marker_color='lightgreen',
                hovertemplate='<b>%{x}</b><br>Gross: Rs. %{y:,.0f}<extra></extra>'
            ))
            
            # Transfers deducted (negative portion)
            fig_upwork.add_trace(go.Bar(
                name='Transfers to Daniyal/Talha',
                x=yearly_income_breakdown['Year'],
                y=-yearly_income_breakdown['Transfer_Amount'],
                marker_color='lightcoral',
                hovertemplate='<b>%{x}</b><br>Transfers: -Rs. %{y:,.0f}<extra></extra>'
            ))
            
            # Net income line
            fig_upwork.add_trace(go.Scatter(
                name='Net Upwork Income',
                x=yearly_income_breakdown['Year'],
                y=yearly_income_breakdown['Net_Upwork_Income'],
                mode='lines+markers',
                line=dict(color='darkgreen', width=4),
                marker=dict(size=8, color='darkgreen'),
                hovertemplate='<b>%{x}</b><br>Net: Rs. %{y:,.0f}<extra></extra>'
            ))
            
            fig_upwork.update_layout(
                title='Yearly Upwork Income - Gross vs Net (After Transfer Deductions)',
                xaxis_title="Year",
                yaxis_title="Amount (Rs.)",
                barmode='relative',
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 100000
                },
                hovermode='x unified'
            )
            
            st.plotly_chart(fig_upwork, use_container_width=True)
            
            # Show Upwork income summary
            st.subheader("📊 Upwork Income Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                total_gross = yearly_income_breakdown['Upwork_Income'].sum()
                st.metric("Total Gross Upwork", f"Rs. {total_gross:,.2f}")
            
            with col2:
                total_transfers = yearly_income_breakdown['Transfer_Amount'].sum()
                st.metric("Total Transfers Out", f"Rs. {total_transfers:,.2f}")
            
            with col3:
                total_net = yearly_income_breakdown['Net_Upwork_Income'].sum()
                st.metric("Total Net Upwork", f"Rs. {total_net:,.2f}")
            
            with col4:
                avg_net_per_year = yearly_income_breakdown['Net_Upwork_Income'].mean()
                st.metric("Avg Net/Year", f"Rs. {avg_net_per_year:,.2f}")
            
            # Detailed Upwork breakdown table
            st.subheader("📋 Upwork Income Breakdown by Year")
            breakdown_table = yearly_income_breakdown[['Year', 'Upwork_Income', 'Transfer_Amount', 'Net_Upwork_Income', 'Transaction_Count']].copy()
            breakdown_table['Upwork_Income'] = breakdown_table['Upwork_Income'].round(2)
            breakdown_table['Transfer_Amount'] = breakdown_table['Transfer_Amount'].round(2)
            breakdown_table['Net_Upwork_Income'] = breakdown_table['Net_Upwork_Income'].round(2)
            breakdown_table = breakdown_table.rename(columns={
                'Year': 'Year',
                'Upwork_Income': 'Gross Upwork Income (Rs.)',
                'Transfer_Amount': 'Transfers Out (Rs.)',
                'Net_Upwork_Income': 'Net Upwork Income (Rs.)',
                'Transaction_Count': 'Upwork Payments'
            })
            st.dataframe(breakdown_table, use_container_width=True)
        else:
            st.info("No Upwork income data found for the selected period")
        
        # Yearly Expenditure Bar Graph (using FILTERED data)
        st.subheader("📊 Yearly Expenditure Summary")
        
        # Calculate yearly expenses (only negative amounts)
        yearly_expenses = df_filtered[df_filtered['Amount'] < 0].groupby('Year').agg({
            'Amount': 'sum',
            'Description': 'count'
        }).reset_index()
        
        # Convert to positive values for the chart
        yearly_expenses['Expenditure'] = abs(yearly_expenses['Amount'])
        yearly_expenses = yearly_expenses.rename(columns={'Description': 'Transaction_Count'})
        yearly_expenses = yearly_expenses.sort_values('Year')
        
        if not yearly_expenses.empty:
            fig_yearly = px.bar(yearly_expenses, 
                              x='Year', 
                              y='Expenditure',
                              title='Yearly Expenditure Summary - Real Expenses (Rs.)',
                              color='Expenditure',
                              color_continuous_scale='blues',
                              hover_data=['Transaction_Count'],
                              text='Expenditure')
            
            fig_yearly.update_layout(
                xaxis_title="Year", 
                yaxis_title="Total Expenditure (Rs.)",
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 100000  # 100k increments
                }
            )
            
            # Format the text on bars
            fig_yearly.update_traces(texttemplate='Rs. %{y:,.0f}', textposition='outside')
            
            st.plotly_chart(fig_yearly, use_container_width=True)
            
            # Show yearly expenditure summary
            st.subheader("💸 Yearly Expenditure Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_yearly_expense = yearly_expenses['Expenditure'].mean()
                st.metric("Average Yearly Spend", f"Rs. {avg_yearly_expense:,.2f}")
            
            with col2:
                max_yearly_expense = yearly_expenses['Expenditure'].max()
                max_year = yearly_expenses.loc[yearly_expenses['Expenditure'].idxmax(), 'Year']
                st.metric("Highest Spending Year", f"Rs. {max_yearly_expense:,.2f}", f"({max_year})")
            
            with col3:
                min_yearly_expense = yearly_expenses['Expenditure'].min()
                min_year = yearly_expenses.loc[yearly_expenses['Expenditure'].idxmin(), 'Year']
                st.metric("Lowest Spending Year", f"Rs. {min_yearly_expense:,.2f}", f"({min_year})")
            
            with col4:
                total_years = len(yearly_expenses)
                st.metric("Total Years", total_years)
                
            # Yearly summary table
            st.subheader("📋 Yearly Breakdown")
            yearly_table = yearly_expenses[['Year', 'Expenditure', 'Transaction_Count']].copy()
            yearly_table['Expenditure'] = yearly_table['Expenditure'].round(2)
            yearly_table['Average per Transaction'] = (yearly_table['Expenditure'] / yearly_table['Transaction_Count']).round(2)
            yearly_table = yearly_table.rename(columns={
                'Year': 'Year',
                'Expenditure': 'Total Expenditure (Rs.)',
                'Transaction_Count': 'Number of Transactions'
            })
            st.dataframe(yearly_table, use_container_width=True)
        else:
            st.info("No yearly expenditure data found for the selected period")
        
        # ... rest of your existing code (Monthly Expenditure, Top 20 Payees, etc.) ...
        # [Keep all the existing sections below - they're already using df_filtered]

    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

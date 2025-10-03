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
        
        st.success(f"✅ Successfully loaded {len(df)} transactions")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            total_income = df[df['Amount'] > 0]['Amount'].sum()
            st.metric("Total Income", f"Rs. {total_income:,.2f}")
        
        with col3:
            total_expenses = abs(df[df['Amount'] < 0]['Amount'].sum())
            st.metric("Total Expenses", f"Rs. {total_expenses:,.2f}")
        
        with col4:
            net_flow = df['Amount'].sum()
            st.metric("Net Flow", f"Rs. {net_flow:,.2f}")
        
        # Balance over time chart - USING ACTUAL BALANCES
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')
        
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
        
        # Yearly Expenditure Bar Graph
        st.subheader("📊 Yearly Expenditure Summary")
        
        # Create year column
        df['Year'] = df['Date'].dt.strftime('%Y')
        
        # Calculate yearly expenses (only negative amounts)
        yearly_expenses = df[df['Amount'] < 0].groupby('Year').agg({
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
                              title='Yearly Expenditure Summary (Rs.)',
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
                                title='Monthly Expenditure (Rs.)',
                                color='Expenditure',
                                color_continuous_scale='reds')
            
            fig_expenses.update_layout(
                xaxis_title="Month", 
                yaxis_title="Expenditure (Rs.)",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 100000  # 100k increments for consistency
                }
            )
            st.plotly_chart(fig_expenses, use_container_width=True)
            
            # Show monthly expenditure summary
            st.subheader("💸 Monthly Expenditure Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_monthly_expense = monthly_expenses['Expenditure'].mean()
                st.metric("Average Monthly Spend", f"Rs. {avg_monthly_expense:,.2f}")
            
            with col2:
                max_monthly_expense = monthly_expenses['Expenditure'].max()
                max_month = monthly_expenses.loc[monthly_expenses['Expenditure'].idxmax(), 'Month_Year']
                st.metric("Highest Spending Month", f"Rs. {max_monthly_expense:,.2f}", f"({max_month})")
            
            with col3:
                min_monthly_expense = monthly_expenses['Expenditure'].min()
                min_month = monthly_expenses.loc[monthly_expenses['Expenditure'].idxmin(), 'Month_Year']
                st.metric("Lowest Spending Month", f"Rs. {min_monthly_expense:,.2f}", f"({min_month})")
        else:
            st.info("No expenditure data found for the selected period")
        
        # Top 20 Payees Bar Chart
        st.subheader("👥 Top 20 Payees")
        
        # Get only expense transactions
        expense_df = df[df['Amount'] < 0].copy()
        
        if not expense_df.empty:
            # Clean description to extract payee names
            def extract_payee(description):
                # Common patterns in Meezan Bank descriptions
                patterns = [
                    r'Money Transferred to\s+([^-]+)',  # "Money Transferred to NAME -"
                    r'to\s+([^-]+)',                   # "to NAME -"
                    r'Paid to\s+([^-]+)',              # "Paid to NAME -"
                    r'Transfer to\s+([^-]+)',          # "Transfer to NAME -"
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, description, re.IGNORECASE)
                    if match:
                        return match.group(1).strip()
                
                # If no pattern matches, return first few words
                words = description.split()
                if len(words) > 3:
                    return ' '.join(words[:3]) + '...'
                return description[:30] + '...' if len(description) > 30 else description
            
            expense_df['Payee'] = expense_df['Description'].apply(extract_payee)
            
            # Group by payee and sum the amounts (convert to positive)
            payee_totals = expense_df.groupby('Payee').agg({
                'Amount': 'sum',
                'Description': 'count'
            }).reset_index()
            
            payee_totals['Amount'] = abs(payee_totals['Amount'])
            payee_totals = payee_totals.rename(columns={'Description': 'Transaction_Count'})
            
            # Get top 20 payees
            top_20_payees = payee_totals.nlargest(20, 'Amount')
            
            if not top_20_payees.empty:
                # Create bar chart with fixed width and 100k increments
                fig_payees = px.bar(top_20_payees, 
                                  x='Payee', 
                                  y='Amount',
                                  title='Top 20 Payees - Total Amount Paid (Rs.)',
                                  color='Amount',
                                  color_continuous_scale='purples',
                                  hover_data=['Transaction_Count'])
                
                fig_payees.update_layout(
                    xaxis_title="Payee",
                    yaxis_title="Total Amount Paid (Rs.)",
                    xaxis={'tickangle': 45, 'categoryorder': 'total descending'},
                    yaxis={
                        'tickformat': ',.0f',
                        'dtick': 100000,  # 100k increments
                        'tick0': 0,
                        'tickmode': 'linear'
                    },
                    height=600,  # Slightly taller for 20 payees
                    width=900,   # Slightly wider for 20 payees
                    showlegend=False
                )
                
                # Display chart with controlled width
                st.plotly_chart(fig_payees, use_container_width=False)
                
                # Show payee summary table
                st.subheader("📋 Payee Summary")
                summary_table = top_20_payees[['Payee', 'Amount', 'Transaction_Count']].copy()
                summary_table['Amount'] = summary_table['Amount'].round(2)
                summary_table = summary_table.rename(columns={
                    'Payee': 'Payee Name',
                    'Amount': 'Total Paid (Rs.)',
                    'Transaction_Count': 'Number of Transactions'
                })
                st.dataframe(summary_table, use_container_width=True)
                
                # Show some stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_paid = top_20_payees['Amount'].sum()
                    st.metric("Total to Top 20", f"Rs. {total_paid:,.2f}")
                with col2:
                    avg_per_payee = top_20_payees['Amount'].mean()
                    st.metric("Average per Payee", f"Rs. {avg_per_payee:,.2f}")
                with col3:
                    total_transactions = top_20_payees['Transaction_Count'].sum()
                    st.metric("Total Transactions", total_transactions)
                    
            else:
                st.info("No payee data available for analysis")
        else:
            st.info("No expense transactions found for payee analysis")
        
        # Monthly summary (income vs expenses)
        st.subheader("📈 Monthly Income vs Expenses")
        
        monthly_income = df[df['Amount'] > 0].groupby('Month_Year')['Amount'].sum().reset_index()
        monthly_income.columns = ['Month_Year', 'Income']
        
        monthly_expenses_comparison = df[df['Amount'] < 0].groupby('Month_Year')['Amount'].sum().reset_index()
        monthly_expenses_comparison['Expenses'] = abs(monthly_expenses_comparison['Amount'])
        monthly_expenses_comparison = monthly_expenses_comparison[['Month_Year', 'Expenses']]
        
        monthly_summary = pd.merge(monthly_income, monthly_expenses_comparison, on='Month_Year', how='outer').fillna(0)
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
            fig_comparison.update_layout(
                barmode='group',
                title='Monthly Income vs Expenses (Rs.)',
                xaxis_title="Month",
                yaxis_title="Amount (Rs.)",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 100000  # 100k increments
                }
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Transaction history
        st.subheader("📋 Recent Transactions")
        st.dataframe(df.sort_values('Date', ascending=False).head(100))
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

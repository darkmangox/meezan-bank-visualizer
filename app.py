import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import numpy as np

st.set_page_config(page_title="Meezan Bank Visualizer", layout="wide")
st.title("🏦 Meezan Bank Statement Visualizer")
st.markdown("Upload your Meezan Bank CSV file to visualize your transactions")

# Exchange rate (you can update this as needed)
EXCHANGE_RATE = 280  # 1 USD = 280 PKR (adjust based on current rate)

# File upload
uploaded_file = st.file_uploader("Choose CSV file", type="csv")

if uploaded_file is not None:
    try:
        # Read data
        df = pd.read_csv(uploaded_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Convert amounts from PKR to USD
        df['Amount_USD'] = df['Amount'] / EXCHANGE_RATE
        if 'Available Balance' in df.columns:
            df['Available_Balance_USD'] = df['Available Balance'] / EXCHANGE_RATE
        
        st.success(f"✅ Successfully loaded {len(df)} transactions")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            total_income = df[df['Amount_USD'] > 0]['Amount_USD'].sum()
            st.metric("Total Income", f"${total_income:,.2f}")
        
        with col3:
            total_expenses = abs(df[df['Amount_USD'] < 0]['Amount_USD'].sum())
            st.metric("Total Expenses", f"${total_expenses:,.2f}")
        
        with col4:
            net_flow = df['Amount_USD'].sum()
            st.metric("Net Flow", f"${net_flow:,.2f}")
        
        # Balance over time chart - USING ACTUAL BALANCES
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')
        
        # Check if Available Balance column exists
        if 'Available_Balance_USD' in df.columns:
            # Use the actual Available Balance from your bank statement
            fig = px.line(df_sorted, x='Date', y='Available_Balance_USD', 
                         title='Actual Account Balance Over Time (From Bank Records)')
            fig.update_layout(yaxis_title="Balance ($)")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show current balance
            current_balance = df_sorted['Available_Balance_USD'].iloc[-1]
            st.metric("Current Balance", f"${current_balance:,.2f}")
        else:
            # Fallback to calculated balance
            df_sorted['Running_Balance_USD'] = df_sorted['Amount_USD'].cumsum()
            fig = px.line(df_sorted, x='Date', y='Running_Balance_USD', 
                         title='Calculated Balance Over Time')
            st.plotly_chart(fig, use_container_width=True)
            st.info("Using calculated balance (no Available Balance column found)")
        
        # Daily Expenses Summary with Trend Lines
        st.subheader("📈 Daily Expenses Summary with Trends")
        
        # Create date column for daily grouping
        df['Date_Formatted'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        
        # Calculate daily expenses (only negative amounts)
        daily_expenses = df[df['Amount_USD'] < 0].groupby('Date_Formatted').agg({
            'Amount_USD': 'sum',
            'Description': 'count'
        }).reset_index()
        
        # Convert to positive values for the chart
        daily_expenses['Expenditure_USD'] = abs(daily_expenses['Amount_USD'])
        daily_expenses = daily_expenses.rename(columns={'Description': 'Transaction_Count'})
        
        # Extract year and month for coloring and analysis
        daily_expenses['Year'] = pd.to_datetime(daily_expenses['Date_Formatted']).dt.year
        daily_expenses['Month'] = pd.to_datetime(daily_expenses['Date_Formatted']).dt.strftime('%Y-%m')
        daily_expenses = daily_expenses.sort_values('Date_Formatted')
        
        if not daily_expenses.empty:
            # Create line chart with different colors for each year
            fig_daily = px.line(daily_expenses, 
                              x='Date_Formatted', 
                              y='Expenditure_USD',
                              title='Daily Expenses Summary with Trends ($)',
                              color='Year',
                              markers=True,
                              line_shape='linear')
            
            # Add solid white trend line that connects through the dots
            daily_expenses_sorted = daily_expenses.sort_values('Date_Formatted')
            
            fig_daily.add_trace(go.Scatter(
                x=daily_expenses_sorted['Date_Formatted'],
                y=daily_expenses_sorted['Expenditure_USD'],
                mode='lines+markers',
                name='Overall Trend',
                line=dict(color='white', width=3),
                marker=dict(color='white', size=3, symbol='circle'),
                hovertemplate='<b>Trend Line</b><br>Date: %{x}<br>Expenditure: $%{y:,.0f}<extra></extra>'
            ))
            
            fig_daily.update_layout(
                xaxis_title="Date",
                yaxis_title="Total Daily Expenditure ($)",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 100  # $100 increments for daily data
                },
                showlegend=True,
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Add value annotations on each point
            fig_daily.update_traces(hovertemplate='<b>Date:</b> %{x}<br><b>Expenditure:</b> $%{y:,.0f}<br><b>Year:</b> %{fullData.name}<extra></extra>')
            
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Daily expenses summary
            st.subheader("📋 Daily Expenses Summary")
            
            # Show last 30 days for better readability
            recent_daily = daily_expenses.tail(30).copy()
            daily_table = recent_daily[['Date_Formatted', 'Expenditure_USD', 'Transaction_Count', 'Year']].copy()
            daily_table['Expenditure_USD'] = daily_table['Expenditure_USD'].round(2)
            daily_table['Average per Transaction'] = (daily_table['Expenditure_USD'] / daily_table['Transaction_Count']).round(2)
            daily_table = daily_table.rename(columns={
                'Date_Formatted': 'Date',
                'Expenditure_USD': 'Total Expenditure ($)',
                'Transaction_Count': 'Number of Transactions',
                'Year': 'Year'
            })
            st.dataframe(daily_table, use_container_width=True)
            
            # Daily statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                current_day_expense = daily_expenses['Expenditure_USD'].iloc[-1]
                st.metric("Current Day", f"${current_day_expense:,.2f}")
            
            with col2:
                avg_daily_expense = daily_expenses['Expenditure_USD'].mean()
                st.metric("Average per Day", f"${avg_daily_expense:,.2f}")
            
            with col3:
                highest_day_expense = daily_expenses['Expenditure_USD'].max()
                highest_day = daily_expenses.loc[daily_expenses['Expenditure_USD'].idxmax(), 'Date_Formatted']
                st.metric("Highest Day", f"${highest_day_expense:,.2f}", f"({highest_day})")
            
            with col4:
                lowest_day_expense = daily_expenses['Expenditure_USD'].min()
                lowest_day = daily_expenses.loc[daily_expenses['Expenditure_USD'].idxmin(), 'Date_Formatted']
                st.metric("Lowest Day", f"${lowest_day_expense:,.2f}", f"({lowest_day})")
                
            # Monthly average comparison
            st.subheader("📊 Monthly Average Daily Expenses")
            
            # Calculate monthly averages
            monthly_avg = daily_expenses.groupby('Month').agg({
                'Expenditure_USD': 'mean',
                'Transaction_Count': 'mean'
            }).reset_index()
            
            monthly_avg = monthly_avg.rename(columns={
                'Expenditure_USD': 'Average Daily Expenditure',
                'Transaction_Count': 'Average Daily Transactions'
            })
            monthly_avg = monthly_avg.sort_values('Month')
            
            if not monthly_avg.empty:
                fig_monthly_avg = px.bar(monthly_avg, 
                                       x='Month', 
                                       y='Average Daily Expenditure',
                                       title='Monthly Average Daily Expenses ($)',
                                       color='Average Daily Expenditure',
                                       color_continuous_scale='greens',
                                       text='Average Daily Expenditure')
                
                fig_monthly_avg.update_layout(
                    xaxis_title="Month", 
                    yaxis_title="Average Daily Expenditure ($)",
                    xaxis={'tickangle': 45},
                    yaxis={
                        'tickformat': ',.0f'
                    }
                )
                
                # Format the text on bars
                fig_monthly_avg.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
                
                st.plotly_chart(fig_monthly_avg, use_container_width=True)
                
                # Monthly average table
                st.subheader("📋 Monthly Averages")
                monthly_avg_table = monthly_avg.copy()
                monthly_avg_table['Average Daily Expenditure'] = monthly_avg_table['Average Daily Expenditure'].round(2)
                monthly_avg_table['Average Daily Transactions'] = monthly_avg_table['Average Daily Transactions'].round(1)
                monthly_avg_table = monthly_avg_table.rename(columns={
                    'Month': 'Month',
                    'Average Daily Expenditure': 'Avg Daily Expenditure ($)',
                    'Average Daily Transactions': 'Avg Daily Transactions'
                })
                st.dataframe(monthly_avg_table, use_container_width=True)
            else:
                st.info("No monthly average data available")
                
        else:
            st.info("No daily expenses data available")
        
        # Yearly Expenditure Bar Graph
        st.subheader("📊 Yearly Expenditure Summary")
        
        # Calculate yearly expenses (only negative amounts)
        yearly_expenses = df[df['Amount_USD'] < 0].groupby('Year').agg({
            'Amount_USD': 'sum',
            'Description': 'count'
        }).reset_index()
        
        # Convert to positive values for the chart
        yearly_expenses['Expenditure_USD'] = abs(yearly_expenses['Amount_USD'])
        yearly_expenses = yearly_expenses.rename(columns={'Description': 'Transaction_Count'})
        yearly_expenses = yearly_expenses.sort_values('Year')
        
        if not yearly_expenses.empty:
            fig_yearly = px.bar(yearly_expenses, 
                              x='Year', 
                              y='Expenditure_USD',
                              title='Yearly Expenditure Summary ($)',
                              color='Expenditure_USD',
                              color_continuous_scale='blues',
                              hover_data=['Transaction_Count'],
                              text='Expenditure_USD')
            
            fig_yearly.update_layout(
                xaxis_title="Year", 
                yaxis_title="Total Expenditure ($)",
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 1000  # $1,000 increments
                }
            )
            
            # Format the text on bars
            fig_yearly.update_traces(texttemplate='$%{y:,.0f}', textposition='outside')
            
            st.plotly_chart(fig_yearly, use_container_width=True)
            
            # Show yearly expenditure summary
            st.subheader("💸 Yearly Expenditure Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_yearly_expense = yearly_expenses['Expenditure_USD'].mean()
                st.metric("Average Yearly Spend", f"${avg_yearly_expense:,.2f}")
            
            with col2:
                max_yearly_expense = yearly_expenses['Expenditure_USD'].max()
                max_year = yearly_expenses.loc[yearly_expenses['Expenditure_USD'].idxmax(), 'Year']
                st.metric("Highest Spending Year", f"${max_yearly_expense:,.2f}", f"({max_year})")
            
            with col3:
                min_yearly_expense = yearly_expenses['Expenditure_USD'].min()
                min_year = yearly_expenses.loc[yearly_expenses['Expenditure_USD'].idxmin(), 'Year']
                st.metric("Lowest Spending Year", f"${min_yearly_expense:,.2f}", f"({min_year})")
            
            with col4:
                total_years = len(yearly_expenses)
                st.metric("Total Years", total_years)
                
            # Yearly summary table
            st.subheader("📋 Yearly Breakdown")
            yearly_table = yearly_expenses[['Year', 'Expenditure_USD', 'Transaction_Count']].copy()
            yearly_table['Expenditure_USD'] = yearly_table['Expenditure_USD'].round(2)
            yearly_table['Average per Transaction'] = (yearly_table['Expenditure_USD'] / yearly_table['Transaction_Count']).round(2)
            yearly_table = yearly_table.rename(columns={
                'Year': 'Year',
                'Expenditure_USD': 'Total Expenditure ($)',
                'Transaction_Count': 'Number of Transactions'
            })
            st.dataframe(yearly_table, use_container_width=True)
        else:
            st.info("No yearly expenditure data found for the selected period")
        
        # Monthly Expenditure Bar Graph
        st.subheader("📊 Monthly Expenditure Bar Chart")
        
        # Calculate monthly expenses for bar chart
        monthly_expenses_bar = df[df['Amount_USD'] < 0].groupby('Month').agg({
            'Amount_USD': 'sum'
        }).reset_index()
        
        # Convert to positive values for the chart
        monthly_expenses_bar['Expenditure_USD'] = abs(monthly_expenses_bar['Amount_USD'])
        monthly_expenses_bar = monthly_expenses_bar.sort_values('Month')
        
        if not monthly_expenses_bar.empty:
            fig_expenses = px.bar(monthly_expenses_bar, 
                                x='Month', 
                                y='Expenditure_USD',
                                title='Monthly Expenditure Bar Chart ($)',
                                color='Expenditure_USD',
                                color_continuous_scale='reds')
            
            fig_expenses.update_layout(
                xaxis_title="Month", 
                yaxis_title="Expenditure ($)",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 500  # $500 increments for monthly data
                }
            )
            st.plotly_chart(fig_expenses, use_container_width=True)
            
            # Show monthly expenditure summary
            st.subheader("💸 Monthly Expenditure Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_monthly_expense = monthly_expenses_bar['Expenditure_USD'].mean()
                st.metric("Average Monthly Spend", f"${avg_monthly_expense:,.2f}")
            
            with col2:
                max_monthly_expense = monthly_expenses_bar['Expenditure_USD'].max()
                max_month = monthly_expenses_bar.loc[monthly_expenses_bar['Expenditure_USD'].idxmax(), 'Month']
                st.metric("Highest Spending Month", f"${max_monthly_expense:,.2f}", f"({max_month})")
            
            with col3:
                min_monthly_expense = monthly_expenses_bar['Expenditure_USD'].min()
                min_month = monthly_expenses_bar.loc[monthly_expenses_bar['Expenditure_USD'].idxmin(), 'Month']
                st.metric("Lowest Spending Month", f"${min_monthly_expense:,.2f}", f"({min_month})")
        else:
            st.info("No expenditure data found for the selected period")
        
        # Top 20 Payees Bar Chart
        st.subheader("👥 Top 20 Payees")
        
        # Get only expense transactions
        expense_df = df[df['Amount_USD'] < 0].copy()
        
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
                'Amount_USD': 'sum',
                'Description': 'count'
            }).reset_index()
            
            payee_totals['Amount_USD'] = abs(payee_totals['Amount_USD'])
            payee_totals = payee_totals.rename(columns={'Description': 'Transaction_Count'})
            
            # Get top 20 payees
            top_20_payees = payee_totals.nlargest(20, 'Amount_USD')
            
            if not top_20_payees.empty:
                # Create bar chart with fixed width and USD increments
                fig_payees = px.bar(top_20_payees, 
                                  x='Payee', 
                                  y='Amount_USD',
                                  title='Top 20 Payees - Total Amount Paid ($)',
                                  color='Amount_USD',
                                  color_continuous_scale='purples',
                                  hover_data=['Transaction_Count'])
                
                fig_payees.update_layout(
                    xaxis_title="Payee",
                    yaxis_title="Total Amount Paid ($)",
                    xaxis={'tickangle': 45, 'categoryorder': 'total descending'},
                    yaxis={
                        'tickformat': ',.0f',
                        'dtick': 500,  # $500 increments
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
                summary_table = top_20_payees[['Payee', 'Amount_USD', 'Transaction_Count']].copy()
                summary_table['Amount_USD'] = summary_table['Amount_USD'].round(2)
                summary_table = summary_table.rename(columns={
                    'Payee': 'Payee Name',
                    'Amount_USD': 'Total Paid ($)',
                    'Transaction_Count': 'Number of Transactions'
                })
                st.dataframe(summary_table, use_container_width=True)
                
                # Show some stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_paid = top_20_payees['Amount_USD'].sum()
                    st.metric("Total to Top 20", f"${total_paid:,.2f}")
                with col2:
                    avg_per_payee = top_20_payees['Amount_USD'].mean()
                    st.metric("Average per Payee", f"${avg_per_payee:,.2f}")
                with col3:
                    total_transactions = top_20_payees['Transaction_Count'].sum()
                    st.metric("Total Transactions", total_transactions)
                    
            else:
                st.info("No payee data available for analysis")
        else:
            st.info("No expense transactions found for payee analysis")
        
        # Monthly summary (income vs expenses)
        st.subheader("📈 Monthly Income vs Expenses")
        
        monthly_income = df[df['Amount_USD'] > 0].groupby('Month').agg({
            'Amount_USD': 'sum'
        }).reset_index()
        monthly_income.columns = ['Month', 'Income_USD']
        
        monthly_expenses_comparison = df[df['Amount_USD'] < 0].groupby('Month').agg({
            'Amount_USD': 'sum'
        }).reset_index()
        monthly_expenses_comparison['Expenses_USD'] = abs(monthly_expenses_comparison['Amount_USD'])
        monthly_expenses_comparison = monthly_expenses_comparison[['Month', 'Expenses_USD']]
        
        monthly_summary = pd.merge(monthly_income, monthly_expenses_comparison, on='Month', how='outer').fillna(0)
        monthly_summary = monthly_summary.sort_values('Month')
        
        if not monthly_summary.empty:
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(name='Income', 
                                          x=monthly_summary['Month'], 
                                          y=monthly_summary['Income_USD'],
                                          marker_color='green'))
            fig_comparison.add_trace(go.Bar(name='Expenses', 
                                          x=monthly_summary['Month'], 
                                          y=monthly_summary['Expenses_USD'],
                                          marker_color='red'))
            fig_comparison.update_layout(
                barmode='group',
                title='Monthly Income vs Expenses ($)',
                xaxis_title="Month",
                yaxis_title="Amount ($)",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': 500  # $500 increments
                }
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Transaction history
        st.subheader("📋 Recent Transactions")
        # Show both PKR and USD amounts
        recent_df = df.sort_values('Date', ascending=False).head(100).copy()
        recent_df['Amount_PKR'] = recent_df['Amount']
        recent_df['Amount_USD'] = recent_df['Amount_USD']
        display_df = recent_df[['Date', 'Description', 'Amount_PKR', 'Amount_USD']]
        display_df = display_df.rename(columns={
            'Amount_PKR': 'Amount (PKR)',
            'Amount_USD': 'Amount (USD)'
        })
        st.dataframe(display_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

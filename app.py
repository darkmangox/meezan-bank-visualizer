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

# Currency state
if 'currency' not in st.session_state:
    st.session_state.currency = 'USD'  # Default currency

# File upload
uploaded_file = st.file_uploader("Choose CSV file", type="csv")

# Currency toggle button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button(f"Switch to {'PKR (Rs.)' if st.session_state.currency == 'USD' else 'USD ($)'}"):
        st.session_state.currency = 'PKR' if st.session_state.currency == 'USD' else 'USD'
    st.write(f"**Current Currency: {st.session_state.currency}**")

def format_currency(amount):
    """Format amount based on selected currency"""
    if st.session_state.currency == 'USD':
        return f"${amount:,.2f}"
    else:
        return f"Rs. {amount:,.2f}"

def get_currency_symbol():
    """Get currency symbol for labels"""
    return "$" if st.session_state.currency == 'USD' else "Rs."

def convert_amount(amount_pkr):
    """Convert amount based on selected currency"""
    if st.session_state.currency == 'USD':
        return amount_pkr / EXCHANGE_RATE
    else:
        return amount_pkr

if uploaded_file is not None:
    try:
        # Read data
        df = pd.read_csv(uploaded_file)
        df['Date'] = pd.to_datetime(df['Date'])
        
        # Convert amounts from PKR to USD for calculations
        df['Amount_USD'] = df['Amount'] / EXCHANGE_RATE
        if 'Available Balance' in df.columns:
            df['Available_Balance_USD'] = df['Available Balance'] / EXCHANGE_RATE
        
        st.success(f"✅ Successfully loaded {len(df)} transactions")
        
        # Display summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Transactions", len(df))
        
        with col2:
            total_income_pkr = df[df['Amount'] > 0]['Amount'].sum()
            total_income = convert_amount(total_income_pkr)
            st.metric("Total Income", format_currency(total_income))
        
        with col3:
            total_expenses_pkr = abs(df[df['Amount'] < 0]['Amount'].sum())
            total_expenses = convert_amount(total_expenses_pkr)
            st.metric("Total Expenses", format_currency(total_expenses))
        
        with col4:
            net_flow_pkr = df['Amount'].sum()
            net_flow = convert_amount(net_flow_pkr)
            st.metric("Net Flow", format_currency(net_flow))
        
        # Balance over time chart - USING ACTUAL BALANCES
        st.subheader("💰 Balance Over Time")
        df_sorted = df.sort_values('Date')
        
        # Check if Available Balance column exists
        if 'Available_Balance_USD' in df.columns:
            # Use the actual Available Balance from your bank statement
            balance_data = df_sorted['Available_Balance_USD' if st.session_state.currency == 'USD' else 'Available Balance']
            fig = px.line(df_sorted, x='Date', y=balance_data, 
                         title=f'Actual Account Balance Over Time (From Bank Records)')
            currency_symbol = get_currency_symbol()
            fig.update_layout(yaxis_title=f"Balance ({currency_symbol})")
            st.plotly_chart(fig, use_container_width=True)
            
            # Show current balance
            current_balance_pkr = df_sorted['Available Balance'].iloc[-1] if 'Available Balance' in df_sorted.columns else 0
            current_balance = convert_amount(current_balance_pkr)
            st.metric("Current Balance", format_currency(current_balance))
        else:
            # Fallback to calculated balance
            running_balance_pkr = df_sorted['Amount'].cumsum()
            running_balance = running_balance_pkr if st.session_state.currency == 'PKR' else running_balance_pkr / EXCHANGE_RATE
            df_sorted['Running_Balance'] = running_balance
            
            fig = px.line(df_sorted, x='Date', y='Running_Balance', 
                         title=f'Calculated Balance Over Time')
            currency_symbol = get_currency_symbol()
            fig.update_layout(yaxis_title=f"Balance ({currency_symbol})")
            st.plotly_chart(fig, use_container_width=True)
            st.info("Using calculated balance (no Available Balance column found)")
        
        # Daily Expenses Summary with Trend Lines
        st.subheader("📈 Daily Expenses Summary with Trends")
        
        # Create date column for daily grouping
        df['Date_Formatted'] = df['Date'].dt.strftime('%Y-%m-%d')
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.strftime('%Y-%m')
        
        # Calculate daily expenses (only negative amounts)
        daily_expenses_pkr = df[df['Amount'] < 0].groupby('Date_Formatted').agg({
            'Amount': 'sum',
            'Description': 'count'
        }).reset_index()
        
        # Convert to positive values for the chart
        daily_expenses_pkr['Expenditure'] = abs(daily_expenses_pkr['Amount'])
        daily_expenses_pkr = daily_expenses_pkr.rename(columns={'Description': 'Transaction_Count'})
        
        # Extract year and month for coloring and analysis
        daily_expenses_pkr['Year'] = pd.to_datetime(daily_expenses_pkr['Date_Formatted']).dt.year
        daily_expenses_pkr['Month'] = pd.to_datetime(daily_expenses_pkr['Date_Formatted']).dt.strftime('%Y-%m')
        daily_expenses_pkr = daily_expenses_pkr.sort_values('Date_Formatted')
        
        # Convert to selected currency
        daily_expenses = daily_expenses_pkr.copy()
        daily_expenses['Expenditure_Display'] = daily_expenses_pkr['Expenditure'].apply(convert_amount)
        
        if not daily_expenses.empty:
            # Create line chart with different colors for each year
            fig_daily = px.line(daily_expenses, 
                              x='Date_Formatted', 
                              y='Expenditure_Display',
                              title=f'Daily Expenses Summary with Trends ({get_currency_symbol()})',
                              color='Year',
                              markers=True,
                              line_shape='linear')
            
            # Add solid white trend line that connects through the dots
            daily_expenses_sorted = daily_expenses.sort_values('Date_Formatted')
            
            fig_daily.add_trace(go.Scatter(
                x=daily_expenses_sorted['Date_Formatted'],
                y=daily_expenses_sorted['Expenditure_Display'],
                mode='lines+markers',
                name='Overall Trend',
                line=dict(color='white', width=3),
                marker=dict(color='white', size=3, symbol='circle'),
                hovertemplate=f'<b>Trend Line</b><br>Date: %{{x}}<br>Expenditure: {get_currency_symbol()}%{{y:,.0f}}<extra></extra>'
            ))
            
            # Set appropriate increments based on currency
            if st.session_state.currency == 'USD':
                dtick_value = 100  # $100 increments for daily data
            else:
                dtick_value = 25000  # Rs. 25,000 increments for daily data
            
            fig_daily.update_layout(
                xaxis_title="Date",
                yaxis_title=f"Total Daily Expenditure ({get_currency_symbol()})",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': dtick_value
                },
                showlegend=True,
                height=500,
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)'
            )
            
            # Add value annotations on each point
            fig_daily.update_traces(hovertemplate=f'<b>Date:</b> %{{x}}<br><b>Expenditure:</b> {get_currency_symbol()}%{{y:,.0f}}<br><b>Year:</b> %{{fullData.name}}<extra></extra>')
            
            st.plotly_chart(fig_daily, use_container_width=True)
            
            # Daily expenses summary
            st.subheader("📋 Daily Expenses Summary")
            
            # Show last 30 days for better readability
            recent_daily = daily_expenses.tail(30).copy()
            daily_table = recent_daily[['Date_Formatted', 'Expenditure_Display', 'Transaction_Count', 'Year']].copy()
            daily_table['Expenditure_Display'] = daily_table['Expenditure_Display'].round(2)
            daily_table['Average per Transaction'] = (daily_table['Expenditure_Display'] / daily_table['Transaction_Count']).round(2)
            daily_table = daily_table.rename(columns={
                'Date_Formatted': 'Date',
                'Expenditure_Display': f'Total Expenditure ({get_currency_symbol()})',
                'Transaction_Count': 'Number of Transactions',
                'Year': 'Year'
            })
            st.dataframe(daily_table, use_container_width=True)
            
            # Daily statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                current_day_expense = daily_expenses['Expenditure_Display'].iloc[-1]
                st.metric("Current Day", format_currency(current_day_expense))
            
            with col2:
                avg_daily_expense = daily_expenses['Expenditure_Display'].mean()
                st.metric("Average per Day", format_currency(avg_daily_expense))
            
            with col3:
                highest_day_expense = daily_expenses['Expenditure_Display'].max()
                highest_day = daily_expenses.loc[daily_expenses['Expenditure_Display'].idxmax(), 'Date_Formatted']
                st.metric("Highest Day", format_currency(highest_day_expense), f"({highest_day})")
            
            with col4:
                lowest_day_expense = daily_expenses['Expenditure_Display'].min()
                lowest_day = daily_expenses.loc[daily_expenses['Expenditure_Display'].idxmin(), 'Date_Formatted']
                st.metric("Lowest Day", format_currency(lowest_day_expense), f"({lowest_day})")
                
            # Monthly average comparison
            st.subheader("📊 Monthly Average Daily Expenses")
            
            # Calculate monthly averages
            monthly_avg = daily_expenses.groupby('Month').agg({
                'Expenditure_Display': 'mean',
                'Transaction_Count': 'mean'
            }).reset_index()
            
            monthly_avg = monthly_avg.rename(columns={
                'Expenditure_Display': 'Average Daily Expenditure',
                'Transaction_Count': 'Average Daily Transactions'
            })
            monthly_avg = monthly_avg.sort_values('Month')
            
            if not monthly_avg.empty:
                fig_monthly_avg = px.bar(monthly_avg, 
                                       x='Month', 
                                       y='Average Daily Expenditure',
                                       title=f'Monthly Average Daily Expenses ({get_currency_symbol()})',
                                       color='Average Daily Expenditure',
                                       color_continuous_scale='greens',
                                       text='Average Daily Expenditure')
                
                fig_monthly_avg.update_layout(
                    xaxis_title="Month", 
                    yaxis_title=f"Average Daily Expenditure ({get_currency_symbol()})",
                    xaxis={'tickangle': 45},
                    yaxis={
                        'tickformat': ',.0f'
                    }
                )
                
                # Format the text on bars
                fig_monthly_avg.update_traces(texttemplate=f'{get_currency_symbol()}%{{y:,.0f}}', textposition='outside')
                
                st.plotly_chart(fig_monthly_avg, use_container_width=True)
                
                # Monthly average table
                st.subheader("📋 Monthly Averages")
                monthly_avg_table = monthly_avg.copy()
                monthly_avg_table['Average Daily Expenditure'] = monthly_avg_table['Average Daily Expenditure'].round(2)
                monthly_avg_table['Average Daily Transactions'] = monthly_avg_table['Average Daily Transactions'].round(1)
                monthly_avg_table = monthly_avg_table.rename(columns={
                    'Month': 'Month',
                    'Average Daily Expenditure': f'Avg Daily Expenditure ({get_currency_symbol()})',
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
        yearly_expenses_pkr = df[df['Amount'] < 0].groupby('Year').agg({
            'Amount': 'sum',
            'Description': 'count'
        }).reset_index()
        
        # Convert to positive values for the chart
        yearly_expenses_pkr['Expenditure'] = abs(yearly_expenses_pkr['Amount'])
        yearly_expenses_pkr = yearly_expenses_pkr.rename(columns={'Description': 'Transaction_Count'})
        yearly_expenses_pkr = yearly_expenses_pkr.sort_values('Year')
        
        # Convert to selected currency
        yearly_expenses = yearly_expenses_pkr.copy()
        yearly_expenses['Expenditure_Display'] = yearly_expenses_pkr['Expenditure'].apply(convert_amount)
        
        if not yearly_expenses.empty:
            fig_yearly = px.bar(yearly_expenses, 
                              x='Year', 
                              y='Expenditure_Display',
                              title=f'Yearly Expenditure Summary ({get_currency_symbol()})',
                              color='Expenditure_Display',
                              color_continuous_scale='blues',
                              hover_data=['Transaction_Count'],
                              text='Expenditure_Display')
            
            # Set appropriate increments based on currency
            if st.session_state.currency == 'USD':
                dtick_value = 1000  # $1,000 increments
            else:
                dtick_value = 100000  # Rs. 100,000 increments
            
            fig_yearly.update_layout(
                xaxis_title="Year", 
                yaxis_title=f"Total Expenditure ({get_currency_symbol()})",
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': dtick_value
                }
            )
            
            # Format the text on bars
            fig_yearly.update_traces(texttemplate=f'{get_currency_symbol()}%{{y:,.0f}}', textposition='outside')
            
            st.plotly_chart(fig_yearly, use_container_width=True)
            
            # Show yearly expenditure summary
            st.subheader("💸 Yearly Expenditure Summary")
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_yearly_expense = yearly_expenses['Expenditure_Display'].mean()
                st.metric("Average Yearly Spend", format_currency(avg_yearly_expense))
            
            with col2:
                max_yearly_expense = yearly_expenses['Expenditure_Display'].max()
                max_year = yearly_expenses.loc[yearly_expenses['Expenditure_Display'].idxmax(), 'Year']
                st.metric("Highest Spending Year", format_currency(max_yearly_expense), f"({max_year})")
            
            with col3:
                min_yearly_expense = yearly_expenses['Expenditure_Display'].min()
                min_year = yearly_expenses.loc[yearly_expenses['Expenditure_Display'].idxmin(), 'Year']
                st.metric("Lowest Spending Year", format_currency(min_yearly_expense), f"({min_year})")
            
            with col4:
                total_years = len(yearly_expenses)
                st.metric("Total Years", total_years)
                
            # Yearly summary table
            st.subheader("📋 Yearly Breakdown")
            yearly_table = yearly_expenses[['Year', 'Expenditure_Display', 'Transaction_Count']].copy()
            yearly_table['Expenditure_Display'] = yearly_table['Expenditure_Display'].round(2)
            yearly_table['Average per Transaction'] = (yearly_table['Expenditure_Display'] / yearly_table['Transaction_Count']).round(2)
            yearly_table = yearly_table.rename(columns={
                'Year': 'Year',
                'Expenditure_Display': f'Total Expenditure ({get_currency_symbol()})',
                'Transaction_Count': 'Number of Transactions'
            })
            st.dataframe(yearly_table, use_container_width=True)
        else:
            st.info("No yearly expenditure data found for the selected period")
        
        # Monthly Expenditure Bar Graph
        st.subheader("📊 Monthly Expenditure Bar Chart")
        
        # Calculate monthly expenses for bar chart
        monthly_expenses_bar_pkr = df[df['Amount'] < 0].groupby('Month').agg({
            'Amount': 'sum'
        }).reset_index()
        
        # Convert to positive values for the chart
        monthly_expenses_bar_pkr['Expenditure'] = abs(monthly_expenses_bar_pkr['Amount'])
        monthly_expenses_bar_pkr = monthly_expenses_bar_pkr.sort_values('Month')
        
        # Convert to selected currency
        monthly_expenses_bar = monthly_expenses_bar_pkr.copy()
        monthly_expenses_bar['Expenditure_Display'] = monthly_expenses_bar_pkr['Expenditure'].apply(convert_amount)
        
        if not monthly_expenses_bar.empty:
            fig_expenses = px.bar(monthly_expenses_bar, 
                                x='Month', 
                                y='Expenditure_Display',
                                title=f'Monthly Expenditure Bar Chart ({get_currency_symbol()})',
                                color='Expenditure_Display',
                                color_continuous_scale='reds')
            
            # Set appropriate increments based on currency
            if st.session_state.currency == 'USD':
                dtick_value = 500  # $500 increments for monthly data
            else:
                dtick_value = 100000  # Rs. 100,000 increments for monthly data
            
            fig_expenses.update_layout(
                xaxis_title="Month", 
                yaxis_title=f"Expenditure ({get_currency_symbol()})",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': dtick_value
                }
            )
            st.plotly_chart(fig_expenses, use_container_width=True)
            
            # Show monthly expenditure summary
            st.subheader("💸 Monthly Expenditure Summary")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                avg_monthly_expense = monthly_expenses_bar['Expenditure_Display'].mean()
                st.metric("Average Monthly Spend", format_currency(avg_monthly_expense))
            
            with col2:
                max_monthly_expense = monthly_expenses_bar['Expenditure_Display'].max()
                max_month = monthly_expenses_bar.loc[monthly_expenses_bar['Expenditure_Display'].idxmax(), 'Month']
                st.metric("Highest Spending Month", format_currency(max_monthly_expense), f"({max_month})")
            
            with col3:
                min_monthly_expense = monthly_expenses_bar['Expenditure_Display'].min()
                min_month = monthly_expenses_bar.loc[monthly_expenses_bar['Expenditure_Display'].idxmin(), 'Month']
                st.metric("Lowest Spending Month", format_currency(min_monthly_expense), f"({min_month})")
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
            payee_totals_pkr = expense_df.groupby('Payee').agg({
                'Amount': 'sum',
                'Description': 'count'
            }).reset_index()
            
            payee_totals_pkr['Amount'] = abs(payee_totals_pkr['Amount'])
            payee_totals_pkr = payee_totals_pkr.rename(columns={'Description': 'Transaction_Count'})
            
            # Convert to selected currency
            payee_totals = payee_totals_pkr.copy()
            payee_totals['Amount_Display'] = payee_totals_pkr['Amount'].apply(convert_amount)
            
            # Get top 20 payees
            top_20_payees = payee_totals.nlargest(20, 'Amount_Display')
            
            if not top_20_payees.empty:
                # Create bar chart with fixed width and appropriate increments
                fig_payees = px.bar(top_20_payees, 
                                  x='Payee', 
                                  y='Amount_Display',
                                  title=f'Top 20 Payees - Total Amount Paid ({get_currency_symbol()})',
                                  color='Amount_Display',
                                  color_continuous_scale='purples',
                                  hover_data=['Transaction_Count'])
                
                # Set appropriate increments based on currency
                if st.session_state.currency == 'USD':
                    dtick_value = 500  # $500 increments
                else:
                    dtick_value = 100000  # Rs. 100,000 increments
                
                fig_payees.update_layout(
                    xaxis_title="Payee",
                    yaxis_title=f"Total Amount Paid ({get_currency_symbol()})",
                    xaxis={'tickangle': 45, 'categoryorder': 'total descending'},
                    yaxis={
                        'tickformat': ',.0f',
                        'dtick': dtick_value,
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
                summary_table = top_20_payees[['Payee', 'Amount_Display', 'Transaction_Count']].copy()
                summary_table['Amount_Display'] = summary_table['Amount_Display'].round(2)
                summary_table = summary_table.rename(columns={
                    'Payee': 'Payee Name',
                    'Amount_Display': f'Total Paid ({get_currency_symbol()})',
                    'Transaction_Count': 'Number of Transactions'
                })
                st.dataframe(summary_table, use_container_width=True)
                
                # Show some stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    total_paid = top_20_payees['Amount_Display'].sum()
                    st.metric("Total to Top 20", format_currency(total_paid))
                with col2:
                    avg_per_payee = top_20_payees['Amount_Display'].mean()
                    st.metric("Average per Payee", format_currency(avg_per_payee))
                with col3:
                    total_transactions = top_20_payees['Transaction_Count'].sum()
                    st.metric("Total Transactions", total_transactions)
                    
            else:
                st.info("No payee data available for analysis")
        else:
            st.info("No expense transactions found for payee analysis")
        
        # Monthly summary (income vs expenses)
        st.subheader("📈 Monthly Income vs Expenses")
        
        monthly_income_pkr = df[df['Amount'] > 0].groupby('Month').agg({
            'Amount': 'sum'
        }).reset_index()
        monthly_income_pkr.columns = ['Month', 'Income']
        
        monthly_expenses_comparison_pkr = df[df['Amount'] < 0].groupby('Month').agg({
            'Amount': 'sum'
        }).reset_index()
        monthly_expenses_comparison_pkr['Expenses'] = abs(monthly_expenses_comparison_pkr['Amount'])
        monthly_expenses_comparison_pkr = monthly_expenses_comparison_pkr[['Month', 'Expenses']]
        
        monthly_summary_pkr = pd.merge(monthly_income_pkr, monthly_expenses_comparison_pkr, on='Month', how='outer').fillna(0)
        monthly_summary_pkr = monthly_summary_pkr.sort_values('Month')
        
        # Convert to selected currency
        monthly_summary = monthly_summary_pkr.copy()
        monthly_summary['Income_Display'] = monthly_summary_pkr['Income'].apply(convert_amount)
        monthly_summary['Expenses_Display'] = monthly_summary_pkr['Expenses'].apply(convert_amount)
        
        if not monthly_summary.empty:
            fig_comparison = go.Figure()
            fig_comparison.add_trace(go.Bar(name='Income', 
                                          x=monthly_summary['Month'], 
                                          y=monthly_summary['Income_Display'],
                                          marker_color='green'))
            fig_comparison.add_trace(go.Bar(name='Expenses', 
                                          x=monthly_summary['Month'], 
                                          y=monthly_summary['Expenses_Display'],
                                          marker_color='red'))
            
            # Set appropriate increments based on currency
            if st.session_state.currency == 'USD':
                dtick_value = 500  # $500 increments
            else:
                dtick_value = 100000  # Rs. 100,000 increments
            
            fig_comparison.update_layout(
                barmode='group',
                title=f'Monthly Income vs Expenses ({get_currency_symbol()})',
                xaxis_title="Month",
                yaxis_title=f"Amount ({get_currency_symbol()})",
                xaxis={'tickangle': 45},
                yaxis={
                    'tickformat': ',.0f',
                    'dtick': dtick_value
                }
            )
            st.plotly_chart(fig_comparison, use_container_width=True)
        
        # Transaction history
        st.subheader("📋 Recent Transactions")
        # Show amounts in selected currency
        recent_df = df.sort_values('Date', ascending=False).head(100).copy()
        recent_df['Amount_Display'] = recent_df['Amount'].apply(convert_amount)
        display_df = recent_df[['Date', 'Description', 'Amount_Display']]
        display_df = display_df.rename(columns={
            'Amount_Display': f'Amount ({get_currency_symbol()})'
        })
        st.dataframe(display_df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error processing file: {e}")
        st.info("Make sure your CSV has columns: Date, Description, Amount, Available Balance")
else:
    st.info("👆 Please upload your Meezan Bank CSV file to begin")

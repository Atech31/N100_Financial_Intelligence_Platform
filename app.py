import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. Page Configuration & Database Connection
# ---------------------------------------------------------
st.set_page_config(page_title="N100 Financial Intelligence", layout="wide")

conn = sqlite3.connect("n100_financial_platform.db")
df = pd.read_sql("SELECT * FROM master_analytics", conn)

st.title("N100 Financial Intelligence Platform")

# ---------------------------------------------------------
# 2. Sidebar Navigation
# ---------------------------------------------------------
page = st.sidebar.radio("Navigation", ["Overview & Screener", "Company Deep Dive", "Sector Intelligence"])

# ---------------------------------------------------------
# PAGE 1: Overview & Screener
# ---------------------------------------------------------
if page == "Overview & Screener":
    st.header("Screener & Universe Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", len(df))
    col2.metric("Median Score", f"{df['health_score'].median():.1f}")
    col3.metric("Excellent Band", len(df[df['health_band'] == 'Excellent']))
    col4.metric("Debt-Free", len(df[df['debt_to_equity'] <= 0.05]))

    st.subheader("Interactive Screener")
    sec = st.multiselect("Select Sector", options=df['broad_sector'].unique(), default=df['broad_sector'].unique())
    min_roe = st.slider("Min ROE (%)", 0.0, 50.0, 10.0)
    
    filtered = df[(df['broad_sector'].isin(sec)) & (df['return_on_equity_pct'] >= min_roe)]
    st.dataframe(
        filtered[['company_id', 'company_name', 'broad_sector', 'market_cap_crore', 'return_on_equity_pct', 'health_score', 'health_band']], 
        width="stretch"
    )

    # Export CSV Feature
    csv_data = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Filtered Results (CSV)",
        data=csv_data,
        file_name="n100_screener_filtered.csv",
        mime="text/csv"
    )

# ---------------------------------------------------------
# PAGE 2: Company Deep Dive
# ---------------------------------------------------------
elif page == "Company Deep Dive":
    comp = st.selectbox("Select Company", df['company_id'].unique())
    c = df[df['company_id'] == comp].iloc[0]
    st.subheader(f"{c['company_name']} ({c['company_id']})")
    st.write(f"**Sector:** {c['broad_sector']} | **Sub-Sector:** {c['sub_sector']}")
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Health Score", f"{c['health_score']}/100", delta=c['health_band'])
    c2.metric("Market Cap (₹ Cr)", f"₹{c['market_cap_crore']:,.2f}" if pd.notnull(c['market_cap_crore']) else "N/A")
    c3.metric("ROE (%)", f"{c['return_on_equity_pct']:.2f}%" if pd.notnull(c['return_on_equity_pct']) else "N/A")

    # Multi-Year Trend Analysis Block
    st.subheader("Historical Financial Trends")

    pnl_df = pd.read_sql(f"SELECT year, sales, net_profit FROM profitandloss WHERE company_id = '{comp}' ORDER BY year", conn)
    cf_df = pd.read_sql(f"SELECT year, free_cash_flow_cr FROM ratios WHERE company_id = '{comp}' ORDER BY year", conn)

    trend_df = pnl_df.merge(cf_df, on='year', how='left')

    fig_trend = px.line(
        trend_df, 
        x='year', 
        y=['sales', 'net_profit', 'free_cash_flow_cr'],
        labels={'value': 'Amount (₹ Cr)', 'variable': 'Metric'},
        title=f"Multi-Year Growth Trajectory for {comp}",
        markers=True
    )
    st.plotly_chart(fig_trend, width="stretch")

# ---------------------------------------------------------
# PAGE 3: Sector Intelligence
# ---------------------------------------------------------
elif page == "Sector Intelligence":
    st.header("Sector Breakdown")
    sec_df = df.groupby('broad_sector').agg(
        Company_Count=('company_id', 'count'), 
        Median_Health=('health_score', 'median')
    ).reset_index()
    
    fig = px.bar(
        sec_df, 
        x='broad_sector', 
        y='Median_Health', 
        color='Median_Health', 
        title="Median Health Score by Sector"
    )
    st.plotly_chart(fig, width="stretch")

    # --- STEP 3: VALUATION MATRIX ---
    st.subheader("Valuation Matrix: P/E vs. ROE")
    fig_scatter = px.scatter(
        df, 
        x='pe_ratio', 
        y='return_on_equity_pct', 
        color='broad_sector',
        hover_name='company_name',
        size='market_cap_crore',
        title="P/E Ratio vs ROE (Bubble size = Market Cap)",
        labels={'pe_ratio': 'P/E Ratio', 'return_on_equity_pct': 'ROE (%)'}
    )
    st.plotly_chart(fig_scatter, width="stretch")



    # ---------------------------------------------------------
# PAGE 1: Overview & Screener
# ---------------------------------------------------------
if page == "Overview & Screener":
    st.header("Screener & Universe Metrics")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Companies", len(df))
    col2.metric("Median Score", f"{df['health_score'].median():.1f}")
    col3.metric("Excellent Band", len(df[df['health_band'] == 'Excellent']))
    col4.metric("Debt-Free", len(df[df['debt_to_equity'] <= 0.05]))

    # --- STEP 4: SECTOR DISTRIBUTION CHART ---
    st.subheader("Market Cap Distribution by Sector")
    sec_weight_df = df.groupby('broad_sector')['market_cap_crore'].sum().reset_index()
    fig_pie = px.pie(
        sec_weight_df, 
        values='market_cap_crore', 
        names='broad_sector', 
        title="Sector Weightage (by Market Cap)",
        hole=0.4 # Makes it a donut chart for a cleaner look
    )
    st.plotly_chart(fig_pie, width="stretch")
    # -----------------------------------------

    st.subheader("Interactive Screener")
    sec = st.multiselect("Select Sector", options=df['broad_sector'].unique(), default=df['broad_sector'].unique(), key="screener_sector")
    min_roe = st.slider("Min ROE (%)", 0.0, 50.0, 10.0, key="screener_min_roe")
    
    filtered = df[(df['broad_sector'].isin(sec)) & (df['return_on_equity_pct'] >= min_roe)]
    st.dataframe(
        filtered[['company_id', 'company_name', 'broad_sector', 'market_cap_crore', 'return_on_equity_pct', 'health_score', 'health_band']], 
        width="stretch"
    )

    # Export CSV Feature
    csv_data = filtered.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download Screener Results (CSV)",
        data=csv_data,
        file_name="n100_screener_filtered.csv",
        mime="text/csv"
    )

    # =========================================================
# ADD NEW PAGE AT THE BOTTOM (DO NOT DELETE PREVIOUS CODE)
# =========================================================
elif page == "Investor Demographics":
    st.header("Investor Demographics & Distribution")
    
    # Top KPI Summary Row
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Active Investors", f"{len(df):,} Users")
    col2.metric("Top Investment Region", "Tier-1 Cities")
    col3.metric("Avg Portfolio Size", "₹1.85 Lakhs")
    
    st.markdown("---")
    
    # Visual 1: Sector Breakdown by Market Cap (Donut Chart)
    st.subheader("Market Cap Distribution by Sector")
    sec_dist = df.groupby('broad_sector')['market_cap_crore'].sum().reset_index()
    fig_demographics = px.pie(
        sec_dist,
        values='market_cap_crore',
        names='broad_sector',
        title="Investor Allocation per Sector",
        hole=0.4
    )
    st.plotly_chart(fig_demographics, width="stretch")
    
    # Visual 2: Demographic Data Table
    st.subheader("Demographic Performance Data")
    st.dataframe(
        df[['company_name', 'broad_sector', 'market_cap_crore', 'health_score', 'health_band']],
        width="stretch"
    )

    # =========================================================
# STEP 1: ADD SEARCH FILTER (Pasted in Investor Demographics block)
# =========================================================
st.subheader("Demographic Performance Data")

# Search and Sector Filter Widgets
col_search, col_filter = st.columns([2, 1])
with col_search:
    search_query = st.text_input("Search Company Name", "", key="demo_search_input")
with col_filter:
    selected_sec = st.selectbox(
        "Filter by Sector", 
        ["All"] + list(df['broad_sector'].unique()), 
        key="demo_sector_select"
    )

# Filter Dataframe based on search inputs
filtered_df = df.copy()
if selected_sec != "All":
    filtered_df = filtered_df[filtered_df['broad_sector'] == selected_sec]

if search_query:
    filtered_df = filtered_df[filtered_df['company_name'].str.contains(search_query, case=False, na=False)]

# Display Filtered Data Table
st.dataframe(
    filtered_df[['company_name', 'broad_sector', 'market_cap_crore', 'health_score', 'health_band']],
    width="stretch"
)

# =========================================================
# STEP 2: DOWNLOAD BUTTON (Pasted right below the table)
# =========================================================
# Convert filtered dataframe to CSV
csv_data = filtered_df.to_csv(index=False).encode('utf-8')

st.download_button(
    label="📥 Download Demographic Data (CSV)",
    data=csv_data,
    file_name="investor_demographics_report.csv",
    mime="text/csv",
    key="demo_download_btn"
)
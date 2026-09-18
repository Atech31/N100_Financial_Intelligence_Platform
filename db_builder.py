import sqlite3
import pandas as pd
import numpy as np
import glob

# Detect files automatically or specify names
files_map = {
    'companies': glob.glob('*companies.xlsx')[0],
    'sectors': glob.glob('*sectors.xlsx')[0],
    'market_cap': glob.glob('*market_cap.xlsx')[0],
    'profitandloss': glob.glob('*profitandloss.xlsx')[0],
    'balancesheet': glob.glob('*balancesheet.xlsx')[0],
    'cashflow': glob.glob('*cashflow.xlsx')[0],
    'ratios': glob.glob('*financial_ratios.xlsx')[0],
    'prices': glob.glob('*stock_prices.xlsx')[0],
    'prosandcons': glob.glob('*prosandcons.xlsx')[0],
    'documents': glob.glob('*documents.xlsx')[0],
    'analysis': glob.glob('*analysis.xlsx')[0]
}

conn = sqlite3.connect("n100_financial_platform.db")

loaded_dfs = {}
for name, fname in files_map.items():
    df_check = pd.read_excel(fname, nrows=2)
    header_idx = 1 if 'id' not in df_check.columns else 0
    df = pd.read_excel(fname, header=header_idx)
    df.to_sql(name, conn, if_exists="replace", index=False)
    loaded_dfs[name] = df

# Consolidate Master Analytics Table
pnl = loaded_dfs['profitandloss'].sort_values('year').groupby('company_id').last().reset_index()
bs = loaded_dfs['balancesheet'].sort_values('year').groupby('company_id').last().reset_index()
cf = loaded_dfs['cashflow'].sort_values('year').groupby('company_id').last().reset_index()
ratios = loaded_dfs['ratios'].sort_values('year').groupby('company_id').last().reset_index()
comp = loaded_dfs['companies']
sec = loaded_dfs['sectors']
mcap = loaded_dfs['market_cap'].sort_values('year').groupby('company_id').last().reset_index()

master_df = comp[['id', 'company_name']].rename(columns={'id': 'company_id'})
master_df = master_df.merge(sec[['company_id', 'broad_sector', 'sub_sector']], on='company_id', how='left')
master_df = master_df.merge(mcap[['company_id', 'market_cap_crore', 'pe_ratio', 'pb_ratio', 'ev_ebitda']], on='company_id', how='left')
master_df = master_df.merge(pnl[['company_id', 'sales', 'operating_profit', 'opm_percentage', 'net_profit']], on='company_id', how='left')
master_df = master_df.merge(ratios[['company_id', 'return_on_equity_pct', 'debt_to_equity', 'interest_coverage', 'free_cash_flow_cr']], on='company_id', how='left')

# Health Score Algorithm (0-100)
def compute_health_score(row):
    score = 0
    roe = row['return_on_equity_pct'] if pd.notnull(row['return_on_equity_pct']) else 0
    if roe >= 20: score += 25
    elif roe >= 15: score += 20
    elif roe >= 10: score += 12
    elif roe > 0: score += 5
    
    de = row['debt_to_equity'] if pd.notnull(row['debt_to_equity']) else 99
    if de <= 0.25: score += 25
    elif de <= 0.5: score += 20
    elif de <= 1.0: score += 12
    elif de <= 1.5: score += 5
    
    opm = row['opm_percentage'] if pd.notnull(row['opm_percentage']) else 0
    if opm >= 22: score += 25
    elif opm >= 15: score += 20
    elif opm >= 10: score += 12
    elif opm > 0: score += 5
    
    fcf = row['free_cash_flow_cr'] if pd.notnull(row['free_cash_flow_cr']) else -1
    if fcf > 0: score += 25
    
    return score

master_df['health_score'] = master_df.apply(compute_health_score, axis=1)

def assign_health_band(score):
    if score >= 80: return 'Excellent'
    elif score >= 65: return 'Good'
    elif score >= 50: return 'Average'
    elif score >= 35: return 'Weak'
    else: return 'Poor'

master_df['health_band'] = master_df['health_score'].apply(assign_health_band)
master_df.to_sql('master_analytics', conn, if_exists='replace', index=False)
print("Database and Master Analytics generated successfully!")

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
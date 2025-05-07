import pandas as pd
import numpy as np
import datetime
from nselib import capital_market
from nselib import derivatives
import json
import Analysis

# Fetch the latest option chain
# df = derivatives.nse_live_option_chain('NIFTY')
# df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date']).dt.date
# op_df = df[['Fetch_Time','Symbol','Expiry_Date','CALLS_LTP','Strike_Price','PUTS_LTP']]
df = Analysis.index_5min_breakout('^NSEI','3d')
print(df)

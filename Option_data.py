import pandas as pd
import numpy as np
import datetime
from nselib import capital_market
from nselib import derivatives
pd.options.display.float_format = '{:.2f}'.format
import os

#NIfty option data
df= derivatives.nse_live_option_chain('NIFTY')
df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date']).dt.date
op_df = df[['Fetch_Time','Symbol','Expiry_Date','CALLS_LTP','Strike_Price','PUTS_LTP']]


final_df = pd.read_csv('final_df.csv')
final_df = pd.concat([final_df,op_df])
final_df.to_csv('final_df.csv',index=False)

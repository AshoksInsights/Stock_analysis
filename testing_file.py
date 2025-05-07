import pandas as pd
import numpy as np
import datetime
from nselib import capital_market
from nselib import derivatives
import json
from libutil import *
from constants import *

# Fetch the latest option chain
# df = derivatives.nse_live_option_chain('NIFTY')
# df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date']).dt.date
# op_df = df[['Fetch_Time','Symbol','Expiry_Date','CALLS_LTP','Strike_Price','PUTS_LTP']]
    
def equity_list():
    """
    get list of all equity available to trade in NSE
    :return: pandas data frame
    """
    origin_url = "https://nsewebsite-staging.nseindia.com"
    url = "https://archives.nseindia.com/content/equities/EQUITY_L.csv"
    file_chk = nse_urlfetch(url,origin_url=origin_url)
    if file_chk.status_code != 200:
        raise FileNotFoundError(f" No data equity list available")
    try:
        data_df = pd.read_csv(BytesIO(file_chk.content))
    except Exception as e:
        raise FileNotFoundError(f' Equity List not found :: NSE error : {e}')
    data_df = data_df[['SYMBOL', 'NAME OF COMPANY', ' SERIES', ' DATE OF LISTING', ' FACE VALUE']]
    return data_df

df = equity_list()
print(df)

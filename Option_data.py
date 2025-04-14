import pandas as pd
import numpy as np
import datetime
from nselib import capital_market
from nselib import derivatives
pd.options.display.float_format = '{:.2f}'.format
import os
import time
from datetime import datetime, time as dt_time
import pytz

# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

def is_market_hours():
    now_ist = datetime.now(IST).time()
    return dt_time(9, 15) <= now_ist <= dt_time(15, 30)

def push_to_git():
    try:
        subprocess.run(["git", "add", "final_df.csv"], check=True)
        subprocess.run(["git", "commit", "-m", f"Update final_df.csv at {datetime.now(IST)}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"Pushed to git at {datetime.now(IST)}")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")

while True:
    now_ist = datetime.now(IST).time()
    # if is_market_hours():
    try:
        # Fetch the latest option chain
        df = derivatives.nse_live_option_chain('NIFTY')
        df['Expiry_Date'] = pd.to_datetime(df['Expiry_Date']).dt.date
        op_df = df[['Fetch_Time','Symbol','Expiry_Date','CALLS_LTP','Strike_Price','PUTS_LTP']]
        
        # Read existing data
        try:
            final_df = pd.read_csv('final_df.csv')
        except FileNotFoundError:
            final_df = pd.DataFrame(columns=op_df.columns)
        
        # Append and save
        final_df = pd.concat([final_df, op_df])
        final_df.to_csv('final_df.csv', index=False)
        
        print(f"Appended data at {datetime.now(IST)}")
    except Exception as e:
        print(f"Error occurred: {e}")
    # else:
        # print(f"Outside market hours: {datetime.now(IST)}")
    
    # if now_ist >= dt_time(15, 30):
    #     print("Market closed. Exiting script.")
    #     break

    time.sleep(60)




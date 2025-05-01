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

import json
import subprocess



# Set IST timezone
IST = pytz.timezone('Asia/Kolkata')

def is_market_hours():
    now_ist = datetime.now(IST).time()
    return dt_time(14, 31) <= now_ist <= dt_time(15, 31)

def push_to_git():
    try:
        subprocess.run(["git","init"])
        # subprocess.run(["git","remote","add","origin" , 'https://github.com/AshoksInsights/Stock_analysis'])
        subprocess.run(["git", "config", "--global", "user.name", 'github-actions[bot]'])
        subprocess.run(["git", "config", "--global", "user.email", 'github-actions[bot]@users.noreply.github.com'])
        subprocess.run(["git", "add", "final_df.csv"], check=True)
        subprocess.run(["git", "commit", "-m", f"Update final_df.csv at {datetime.now(IST)}"], check=True)
        subprocess.run(["git", "push"], check=True)
        print(f"Pushed to git at {datetime.now(IST)}")
    except subprocess.CalledProcessError as e:
        print(f"Git error: {e}")

while True:
    now_ist = datetime.now(IST).time()
    if is_market_hours():
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
                    
            push_to_git()
        except Exception as e:
            print(f"Error occurred: {e}")
    else:
        print("Out of market hours")
    
    if now_ist >= dt_time(15, 31):
        print("Market closed. Exiting script.")
        break

    time.sleep(60)




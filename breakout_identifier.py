import os
import Analysis
import pandas as pd
import numpy as np
import pandas_ta as ta
import yfinance as yf
# import matplotlib.pyplot as plt
# import matplotlib.dates as mdates
# import plotly.graph_objects as go
import datetime
# from collections import Counter
# import multiprocessing as mp
# import time
from nselib import capital_market
from nselib import derivatives
# import plotly.io as pio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pretty_html_table import build_table
my_variable = os.getenv('AUTO_MAIL')


#taking the list from nse
equity_list = pd.read_csv('equity.csv')
equity_list['days'] = ((datetime.datetime.now()) - pd.to_datetime(equity_list[' DATE OF LISTING'],format='%d-%b-%Y')).dt.days
tick = (equity_list[equity_list['days']>60]['SYMBOL']+ '.NS').values.tolist()

#find the nifty_50
nifty_50 = pd.read_csv('nifty50.csv')['Symbol'].to_list()

df1,failed = Analysis.fetch_stock(tick)
df2,failed1 = Analysis.failed_stock(failed)

Final_stocks = pd.concat([df1,df2])

try:
  new_data = Final_stocks[((Final_stocks['breakout_down'] == "Breakout") | (Final_stocks['breakout_down'] == "St Breakout")) & (Final_stocks['Date'] == datetime.date.today())][['symbol', 'Date', 'Close']]
  new_data['current_close'] = [[] for _ in range(len(new_data))]
  new_data['pct_chg'] = [[] for _ in range(len(new_data))]
  existing = pd.read_csv('daily_stock_data.csv')
  # Append new data and drop duplicates if needed
  combined = pd.concat([existing, new_data], ignore_index=True)
  combined.drop_duplicates(subset=['symbol', 'Date'], keep='last', inplace=True)
  combined.to_csv('daily_stock_data.csv', index=False)
except Exception as e:
   pass

Breakout_stocks = Final_stocks[Final_stocks['breakout_down'] == "Breakout"]
Breakdown_stocks = Final_stocks[Final_stocks['breakout_down'] == "Breakdown"]
St_breakout = Final_stocks[Final_stocks['breakout_down'] == "St Breakout"]
St_breadown = Final_stocks[Final_stocks['breakout_down'] == "St Breakdown"]

#Breakout
try:
  today = Breakout_stocks[Breakout_stocks['Date'] == datetime.date.today()][['symbol','Date','Close','Vwap','pct','Volume','vol_chg','average_Volume_30','next_targets','rsi']]
except :
  today = pd.DataFrame()

try:
  today['nifty_50']= np.where(today['symbol'].isin(nifty_50),"NIFTY-50","No")
except:
  pass


if len(today) == 0:
    output = "<h1>No Breakout today</h1>"  # HTML for the message
else:
    output = build_table(today, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
                         text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')

#Breakdown
try:
  today_breakdown = Breakdown_stocks[Breakdown_stocks['Date'] == datetime.date.today()][['symbol','Date','Close','Vwap','pct','Volume','vol_chg','average_Volume_30','next_targets','rsi']]
except:
  today_breakdown = pd.DataFrame()

try:
    today_breakdown['nifty_50']= np.where(today_breakdown['symbol'].isin(nifty_50),"NIFTY-50","No")
except:
  pass

if len(today_breakdown) == 0:
    output_breakdown = "<h1>No Breakdown today</h1>"  # HTML for the message
else:
    output_breakdown = build_table(today_breakdown, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
                     text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')
    
#Supertrend breakout
try:
  today_stbreakout = St_breakout[St_breakout['Date'] == datetime.date.today()][['symbol','Date','Close','Vwap','pct','Volume','vol_chg','average_Volume_30','next_targets','rsi']]
except:
  today_stbreakout = pd.DataFrame()

try:
    today_stbreakout['nifty_50']= np.where(today_stbreakout['symbol'].isin(nifty_50),"NIFTY-50","No")
except:
  pass

if len(today_stbreakout) == 0:
    output_stbreakout = "<h1>No Super Trend Breakout today</h1>"  # HTML for the message
else:
    output_stbreakout = build_table(today_stbreakout, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
                     text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')
    
#Supertrend breakdown
try:
  today_stbreakdown = St_breadown[St_breadown['Date'] == datetime.date.today()][['symbol','Date','Close','Vwap','pct','Volume','vol_chg','average_Volume_30','next_targets','rsi']]
except:
  today_stbreakdown = pd.DataFrame()

try:
    today_stbreakdown['nifty_50']= np.where(today_stbreakdown['symbol'].isin(nifty_50),"NIFTY-50","No")
except:
  pass

if len(today_stbreakdown) == 0:
    output_stbreakdown = "<h1>No Super Trend Breakdown today</h1>"  # HTML for the message
else:
    output_stbreakdown = build_table(today_stbreakdown, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
                     text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')

# fun = []
# for i in today['symbol']:
#   try:
#     s = i + '.NS'
#     fun.append(Analysis.fundamental_data(s))
#   except:
#     None
# if len(fun) == 0:
#   fundamental = pd.DataFrame()
# else:
#   fundamental = pd.concat(fun)

# fundamental_df =  build_table(fundamental, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
#                      text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')

# figs = []
# for symbol in today['symbol']:
#   try:
#     s = symbol + '.NS'
#     # Assuming Analysis.screen4plot returns a DataFrame for the given symbol and interval
#     df1 = Analysis.screen4plot(s,'1d')
#     fig = Analysis.plot(df1, symbol)
#     figs.append(fig)
#   except:
#     pass

# # Combine all figures into a single HTML file
# html_str = ""
# for fig in figs:
#     html_str += pio.to_html(fig)

# with open("combined_plot.html", "w") as file:
#     file.write(html_str)

# print("The combined plot has been saved as combined_plot.html.")

#send email
Analysis.send_mail(output,output_breakdown,output_stbreakout,output_stbreakdown)

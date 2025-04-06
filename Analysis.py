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
import time
from nselib import capital_market
# pd.set_option('display.max_columns', None)
# import plotly.io as pio
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pretty_html_table import build_table
# from dotenv import load_dotenv
import os
# load_dotenv('/content/drive/My Drive/Colab Notebooks/stock_analysis/.env')
my_variable = os.getenv('AUTO_MAIL')

#Function to calculate the window average
def window_average(df,col,p):
  arr = np.array(df[col])
  lt = []
  for i in range(len(arr)):
    if i > p-1:
      lt.append(arr[i-p:i].mean())
    else:
      lt.append(np.nan)
  df[f'average_{col}'] = lt
  return df


#function to calculate smoothed moving average
def calculate_smma(df, period):
    smma = []
    for i in range(len(df)):
        if i < period:
            smma.append(None)  # Not enough data to calculate SMMA
        elif i == period:
            smma.append(df['Close'][:period].mean())  # Initial SMMA value
        else:
            smma_value = (smma[-1] * (period - 1) + df['Close'][i]) / period
            smma.append(smma_value)
    return smma

#function to calculate fibonacci pivot points
def calculate_fibonacci_pivots(df):
    df['Pivot'] = (df['High'].shift(1) + df['Low'].shift(1) + df['Close'].shift(1)) / 3
    df['R1'] = df['Pivot'] + 0.382 * (df['High'].shift(1) - df['Low'].shift(1))
    df['R2'] = df['Pivot'] + 0.618 * (df['High'].shift(1) - df['Low'].shift(1))
    df['R3'] = df['Pivot'] + (df['High'].shift(1) - df['Low'].shift(1))
    df['S1'] = df['Pivot'] - 0.382 * (df['High'].shift(1) - df['Low'].shift(1))
    df['S2'] = df['Pivot'] - 0.618 * (df['High'].shift(1) - df['Low'].shift(1))
    df['S3'] = df['Pivot'] - (df['High'].shift(1) - df['Low'].shift(1))
    return df

#Function to find monthly_pivots
def monthly_pivots(tick,p):
  df = yf.download(tick,period = p , interval = '1mo' , multi_level_index = False ,rounding = True).reset_index()
  df['symbol'] = tick.split('.')[0]
  window_average(df,'Volume',3)
  calculate_fibonacci_pivots(df)
  return df

#Function to find the next targets
def next_targets(row):
    close = row['Close']
    targets = [row['Pivot'], row['R1'], row['R2'], row['R3'], row['S1'], row['S2'], row['S3']]
    targets_greater_than_close = sorted([t for t in targets if t > close])
    return [round(t,2) for t in targets_greater_than_close[:3]]

#function to screen single stock
def stock_screen(ticker,p):
  df = yf.download(ticker, period = p , interval = '1d')
  df = df.droplevel(1,axis=1).reset_index()
  df['symbol'] = ticker.split('.')[0]
  df['smma'] = calculate_smma(df, period=7)
  df['rsi'] = ta.rsi(df['Close'])
  df['pct'] = (df['Close'].pct_change())*100
  df['dema'] = ta.dema(df['Close'], length=10)
  window_average(df,'Volume',30)
  df.rename(columns={'average_Volume':'average_Volume_30'},inplace = True)
  df['vol_chg'] = ((df['Volume'] - df['average_Volume_30']) / df['average_Volume_30'] ) * 100
  df['super_trend'] = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)['SUPERT_10_3.0']
  df['super_trend_color'] = np.where(df['Close'] > df['super_trend'] , "green" , "red")
  df['BBM'] = ta.bbands(close = df['Close'], length=20, std=2)['BBM_20_2.0']
  # df = calculate_fibonacci_pivots(df)
  #identify the position it changes from green to red or viceversa, insert 0 at initial position to avoid blank
  df['changeover'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'green' , 1 , 0)),0,0)
  df['changeover2'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'red' , 1 , 0)),0,0)
  df['condition'] = np.insert(np.diff(np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)),0,0)
  df['condition2'] = np.insert(np.diff(np.where((df['BBM'] > df['smma']) & (df['smma'] > df['dema']) ,1,0)),0,0)
  df['breakout_down'] = np.where((df['changeover'] == 1) & (df['condition'] == 1),"Breakout",np.where((df['changeover2']     == 1) & (df['condition2'] == 1),"Breakdown",np.nan))
  # np.where(df['changeover'] == 1 & df['condition'] == 1)
  df = df.iloc[np.where(((df['changeover'] == 1) & (df['condition'] == 1)) | ((df['changeover2'] == 1) &                        (df['condition2'] == 1)))]
  monthly = pd.read_csv('monthly_pivots.csv')
  monthly['Date'] = pd.to_datetime(monthly['Date'])
  df = df.merge(monthly[['Pivot','R1','R2','R3','S1','S2','S3']], left_on = [df['symbol'],df['Date'].dt.month , df['Date'].dt.year] , right_on = [monthly['symbol'],monthly['Date'].dt.month , monthly['Date'].dt.year] )
  df.drop(columns = ['key_1','key_0','key_2'], axis = 1 ,inplace = True )
  df['next_targets'] = df.apply(next_targets,axis=1)
  df = df[['symbol','Date','Close','pct','Volume','vol_chg','average_Volume_30','next_targets','breakout_down','rsi']]
  return df

#Function to fetch bulk of stocks
def fetch_stock(tick):
    start_time = datetime.datetime.now()
    df_list = []
    failed = []

    for ticker in tick:
        try:
            try:
                df1 = stock_screen(ticker, '1y')
            except Exception as e:
                print(f"Trying with interval='max' for {ticker} due to error: {e}")
                df1 = stock_screen(ticker, 'max')
            df_list.append(df1)
        except Exception as e:
            print(f"Failed to fetch data for {ticker} due to error: {e}")
            failed.append(ticker)
            time.sleep(5)

    end_time = datetime.datetime.now()
    print(f'Total time taken: {(end_time - start_time).seconds} seconds')

    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date
    else:
        final_df = pd.DataFrame()  # Return an empty DataFrame if df_list is empty

    return final_df, failed
#function to fetch failed bulk stocks
def failed_stock(failed):
    if not failed:
        return pd.DataFrame(), []

    start_time = datetime.datetime.now()
    df_list = []
    failed1 = []

    for ticker in failed:
        try:
            try:
                df1 = stock_screen(ticker, '1y')
            except Exception as e:
                print(f"Trying with interval='max' for {ticker} due to error: {e}")
                df1 = stock_screen(ticker, 'max')
            df_list.append(df1)
        except Exception as e:
            print(f"Failed to fetch data for {ticker} due to error: {e}")
            failed1.append(ticker)
            time.sleep(5)

    end_time = datetime.datetime.now()
    print(f'Total time taken for retry: {(end_time - start_time).seconds} seconds')

    if df_list:
        final_df = pd.concat(df_list, ignore_index=True)
        final_df['Date'] = pd.to_datetime(final_df['Date']).dt.date
    else:
        final_df = pd.DataFrame()  # Return an empty DataFrame if df_list is empty

    return final_df, failed1



#function to screen index 5 minutes
def index_5min_breakout(ticker,p):
  # yf.download('INFY.NS',interval='1m',period = '1d',ignore_tz = True,multi_level_index=False)
  df = yf.download(ticker, period = p , interval = '5m',ignore_tz = True,multi_level_index=False)
  df = df.reset_index()
  # df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
  df['symbol'] = ticker.split('.')[0]
  df['month'] = df['Datetime'].dt.month_name()
  df['smma'] = calculate_smma(df, period=7)
  df['rsi'] = ta.rsi(df['Close'])
  df['pct'] = df['Close'].pct_change()
  df['dema'] = ta.dema(df['Close'], length=10)
  df['super_trend'] = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)['SUPERT_10_3.0']
  df['super_trend_color'] = np.where(df['Close'] > df['super_trend'] , "green" , "red")
  df['BBM'] = ta.bbands(close = df['Close'], length=20, std=2)['BBM_20_2.0']
  # df = calculate_fibonacci_pivots(df)
  #identify the position it changes from green to red or viceversa, insert 0 at initial position to avoid blank
  df['changeover'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'green' , 1 , 0)),0,0)
  df['condition'] = np.insert(np.diff(np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)),0,0)
  # np.where(df['changeover'] == 1 & df['condition'] == 1)
  df = df.iloc[np.where((df['changeover'] == 1) & (df['condition'] == 1))]
  # monthly = yf.download(ticker , period = '3mo' , interval = '1d')
  # monthly = monthly.droplevel(1,axis=1).reset_index()
  # monthly = calculate_fibonacci_pivots(monthly)
  # df = df.merge(monthly[['Pivot','R1','R2','R3','S1','S2','S3']], left_on = [df['Datetime'].dt.month , df['Datetime'].dt.year] , right_on = [monthly['Date'].dt.month , monthly['Date'].dt.year] )
  # df.drop(columns = ['key_1','key_0'], axis = 1 ,inplace = True )
  return df

#check the index with 5 minutes changeover
def index_stbreakout_5minutes(ticker,p):
  df = yf.download(ticker, period = p , interval = '5m',ignore_tz = True,multi_level_index=False)
  df = df.reset_index()
  # df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
  # df['symbol'] = ticker.split('.')[0]
  df['month'] = df['Datetime'].dt.month_name()
  df['smma'] = calculate_smma(df, period=7)
  df['rsi'] = ta.rsi(df['Close'])
  df['pct'] = df['Close'].pct_change()
  df['dema'] = ta.dema(df['Close'], length=10)
  df['super_trend'] = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)['SUPERT_10_3.0']
  df['super_trend_color'] = np.where(df['Close'] > df['super_trend'] , "green" , "red")
  df['BBM'] = ta.bbands(close = df['Close'], length=20, std=2)['BBM_20_2.0']
  # df = calculate_fibonacci_pivots(df)
  #identify the position it changes from green to red or viceversa, insert 0 at initial position to avoid blank
  df['changeover'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'green' , 1 , 0)),0,0)
  df['condition'] = np.insert(np.diff(np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)),0,0)
  # np.where(((df['changeover'] == 1)|(df['changeover'] == -1))& (df['condition'] == 1))
  df = df.iloc[np.where(((df['changeover'] == 1)|(df['changeover'] == -1)))]
  # monthly = yf.download(ticker , period = '3mo' , interval = '1d')
  # monthly = monthly.droplevel(1,axis=1).reset_index()
  # monthly = calculate_fibonacci_pivots(monthly)
  # df = df.merge(monthly[['Pivot','R1','R2','R3','S1','S2','S3']], left_on = [df['Datetime'].dt.month , df['Datetime'].dt.year] , right_on = [monthly['Date'].dt.month , monthly['Date'].dt.year] )
  # df.drop(columns = ['key_1','key_0'], axis = 1 ,inplace = True )
  return df

def screen4plot(ticker,p):
  df = yf.download(ticker, period = p , interval = '5m',ignore_tz = True,multi_level_index=False).reset_index()
  df['smma'] = calculate_smma(df, period=7)
  df['dema'] = ta.dema(df['Close'], length=10)
  df['super_trend'] = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)['SUPERT_10_3.0']
  df['super_trend_color'] = np.where(df['Close'] > df['super_trend'] , "green" , "red")
  df['BBM'] = ta.bbands(close = df['Close'], length=20, std=2)['BBM_20_2.0']
  #identify the position it changes from green to red or viceversa, insert 0 at initial position to avoid blank
  df['changeover'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'green' , 1 , 0)),0,0)
  df['condition'] = np.insert(np.diff(np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)),0,0)
  # np.where(((df['changeover'] == 1)|(df['changeover'] == -1))& (df['condition'] == 1))
  return df

# def plot(df,s):
#   fig = go.Figure(data = go.Candlestick(x=df['Datetime'],open=df['Open'],high=df['High'],low=df['Low'],close=df['Close'],name='candle'))
#   fig.add_trace(go.Scatter(x=df['Datetime'],y=df['dema'],name = 'dema'))
#   fig.add_trace(go.Scatter(x=df['Datetime'],y=df['smma'],name = 'smma'))
#   fig.add_trace(go.Scatter(x=df['Datetime'],y=df['BBM'],name = 'BBM'))
#   for i in range(len(df) - 1):
#       fig.add_trace(go.Scatter(
#           x=df['Datetime'][i:i+2],
#           y=df['super_trend'][i:i+2],
#           mode='lines',
#           showlegend = False,
#           line=dict(color=df['super_trend_color'][i])
#       ))
#   # fig.add_trace(go.Scatter(x=df[df['changeover'] != 0]['Datetime'] , y = df[df['changeover'] != 0]['super_trend'] , mode = 'markers'))
#   for index, row in df[df['changeover'] != 0].iterrows():
#     marker_symbol = 'arrow-up' if row['changeover'] == 1 else 'arrow-down'
#     marker_color = 'green' if row['changeover'] == 1 else 'red'

#     fig.add_trace(go.Scatter(
#         x=[row['Datetime']],
#         y=[row['super_trend']],
#         mode='markers',
#         marker=dict(symbol=marker_symbol, color=marker_color, size=10),
#         name='changeover'
#     ))
#   fig.update_layout(
#     title=f"5 min Candle stick chart of {s}",
#     xaxis_title='Datetime',
#     yaxis_title='Price',
#     yaxis=dict(range = [min(df['Close'])-15, max(df['Close'])+15],fixedrange = False),  # Enable y-axis zooming,
#     dragmode='zoom'

# )
      
#   return fig

def fundamental_data(tick):
    # ticker = yf.Ticker(tick).info
    ls = [{
        'symbol': yf.Ticker(tick).info.get('symbol', '').split('.')[0],
        'industry': yf.Ticker(tick).info.get('industry', ''),
        'sector': yf.Ticker(tick).info.get('sector', ''),
        'marketCap': yf.Ticker(tick).info.get('marketCap', ''),
        'currentRatio': yf.Ticker(tick).info.get('currentRatio', ''),
        'returnOnAssets': yf.Ticker(tick).info.get('returnOnAssets', ''),
        'dividendRate': yf.Ticker(tick).info.get('dividendRate', ''),
        'dividendYield': yf.Ticker(tick).info.get('dividendYield', ''),
        'payoutRatio': yf.Ticker(tick).info.get('payoutRatio', ''),
        'beta': yf.Ticker(tick).info.get('beta', ''),
        'trailingPE': yf.Ticker(tick).info.get('trailingPE', ''),
        'forwardPE': yf.Ticker(tick).info.get('forwardPE', ''),
        'volume': yf.Ticker(tick).info.get('volume', ''),
        'profitMargins': yf.Ticker(tick).info.get('profitMargins', ''),
        'sharesOutstanding': yf.Ticker(tick).info.get('sharesOutstanding', ''),
        'bookValue': yf.Ticker(tick).info.get('bookValue', ''),
        'priceToBook': yf.Ticker(tick).info.get('priceToBook', ''),
        'earningsQuarterlyGrowth': yf.Ticker(tick).info.get('earningsQuarterlyGrowth', ''),
        'trailingEps': yf.Ticker(tick).info.get('trailingEps', ''),
        'forwardEps': yf.Ticker(tick).info.get('forwardEps', ''),
        'trailingPegRatio': yf.Ticker(tick).info.get('trailingPegRatio', ''),
        'totalCashPerShare': yf.Ticker(tick).info.get('totalCashPerShare', ''),
        'ebitda': yf.Ticker(tick).info.get('ebitda', ''),
        'totalDebt': yf.Ticker(tick).info.get('totalDebt', ''),
        'totalRevenue': yf.Ticker(tick).info.get('totalRevenue', ''),
        'revenueGrowth': yf.Ticker(tick).info.get('revenueGrowth', ''),
        'grossMargins': yf.Ticker(tick).info.get('grossMargins', ''),
        'debtToEquity': yf.Ticker(tick).info.get('debtToEquity', ''),
        'revenuePerShare': yf.Ticker(tick).info.get('revenuePerShare', ''),
        'returnOnEquity': yf.Ticker(tick).info.get('returnOnEquity', ''),
        'overall risk':yf.Ticker(tick).info.get('overallRisk','')
    }]
    return pd.DataFrame(ls)

def send_mail(output,output_breakdown):
  sender_email = 'ragothaman4010@gmail.com'
  receiver_email = ['ragothaman4010@gmail.com','narendran2cool@gmail.com ','esyuvaraj@gmail.com','sriganishka@gmail.com']
  #receiver_email = ['ragothaman4010@gmail.com']
  subject = 'Today Breakout Stocks'
  body = f"""
  <html>
    <body>
      <p><h3>Hi,</h3><br>
        Please find the Today's Breakout Stocks below:<br>
      </p>
      {output}
        <br>
        Today's Breakdown Stocks:<br>
      </p>
      {output_breakdown}
      <br>
      <h3>
      Regards,<br>
      LIGTHS Team
      </h3>
    </body>
  </html>
  """
  if not my_variable:
        print("AUTO_MAIL environment variable is not set. Email not sent.")
        return
  # Create MIME message
  msg = MIMEMultipart('alternative')
  msg['Subject'] = subject
  msg['From'] = sender_email
  msg['To'] = ', '.join(receiver_email)

  # Attach the HTML body
  msg.attach(MIMEText(body, 'html'))

  # # Attach the plot.html file
  # filename = "combined_plot.html"
  # with open(filename, "rb") as attachment:
  #     part = MIMEBase("application", "octet-stream")
  #     part.set_payload(attachment.read())

  # # Encode file in ASCII characters to send by email    
  # encoders.encode_base64(part)

  # # Add header as key/value pair to attachment part
  # part.add_header(
  #     "Content-Disposition",
  #     f"attachment; filename= {filename}",
  # )

  # # Attach the file to the message
  # msg.attach(part)

  # Send the email
  with smtplib.SMTP('smtp.gmail.com', 587) as server:
      server.starttls()
      server.login(sender_email, my_variable)
      server.sendmail(sender_email, receiver_email, msg.as_string())

  print("Email sent successfully!")


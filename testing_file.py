import pandas as pd 
import numpy as np
import datetime
import Analysis
import pandas_ta as ta
import yfinance as yf
import time
from datetime import datetime, time as dt_time
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pretty_html_table import build_table
import pytz
import os
my_variable = os.getenv('AUTO_MAIL')

def index_5min_breakout(ticker,p):
  # yf.download('INFY.NS',interval='1m',period = '1d',ignore_tz = True,multi_level_index=False)
  df = yf.download(ticker, period = p , interval = '5m',ignore_tz = True,multi_level_index=False)
  df = df.reset_index()
  # df['Datetime'] = df['Datetime'].dt.tz_convert('Asia/Kolkata')
  df['symbol'] = ticker.split('.')[0]
  df['month'] = df['Datetime'].dt.month_name()
  df['smma'] = Analysis.calculate_smma(df, period=7)
  df['rsi'] = ta.rsi(df['Close'])
  df['pct'] = df['Close'].pct_change()
  df['dema'] = ta.dema(df['Close'], length=10)
  df['super_trend'] = ta.supertrend(df['High'], df['Low'], df['Close'], length=10, multiplier=3)['SUPERT_10_3.0']
  df['super_trend_color'] = np.where(df['Close'] > df['super_trend'] , "green" , "red")
  df['BBM'] = ta.bbands(close = df['Close'], length=20, std=2)['BBM_20_2.0']
  # df = calculate_fibonacci_pivots(df)
  #identify the position it changes from green to red or viceversa, insert 0 at initial position to avoid blank
  df['changeover'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'green' , 1 , 0)),0,0)
  df['changeover2'] = np.insert(np.diff(np.where(df['super_trend_color'] == 'red' , 1 , 0)),0,0)
  # df['condition'] = np.insert(np.diff(np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)),0,0)
  # df['condition2'] = np.insert(np.diff(np.where((df['BBM'] > df['smma']) & (df['smma'] > df['dema']) ,1,0)),0,0)
  # df['breakout_down'] = np.where((df['changeover'] == 1) & (df['condition'] == 1),"Breakout",np.where((df['changeover2']     == 1) & (df['condition2'] == 1),"Breakdown",np.nan))
  condition1 = np.where((df['BBM'] < df['smma']) & (df['smma'] < df['dema']) ,1,0)
  condition2 = np.where((df['BBM'] > df['smma']) & (df['smma'] > df['dema']) ,1,0)
  df['breakout_down'] = np.where((df['changeover'] == 1) & (condition1),"Breakout",np.where((df['changeover2']== 1) & (condition2),"Breakdown",np.nan))
  
  # np.where(df['changeover'] == 1 & df['condition'] == 1)
  # df = df.iloc[np.where(((df['changeover'] == 1) & (df['condition'] == 1)) | ((df['changeover2'] == 1) & (df['condition2'] == 1)))]
  df = df.iloc[np.where(((df['changeover'] == 1) & (condition1)) | ((df['changeover2'] == 1) & (condition2)))]
  
  # monthly = yf.download(ticker , period = '3mo' , interval = '1d')
  # monthly = monthly.droplevel(1,axis=1).reset_index()
  # monthly = calculate_fibonacci_pivots(monthly)
  # df = df.merge(monthly[['Pivot','R1','R2','R3','S1','S2','S3']], left_on = [df['Datetime'].dt.month , df['Datetime'].dt.year] , right_on = [monthly['Date'].dt.month , monthly['Date'].dt.year] )
  # df.drop(columns = ['key_1','key_0'], axis = 1 ,inplace = True )
  return df

def send_mail(output):
  sender_email = 'ragothaman4010@gmail.com'
  receiver_email = ['ragothaman4010@gmail.com','narendran2cool@gmail.com ','esyuvaraj@gmail.com','sriganishka@gmail.com']
  # receiver_email = ['ragothaman4010@gmail.com']
  subject = 'Today option calls'
  body = f"""
  <html>
    <body>
      <p><h3>Hi,</h3><br>
        Please find the Today's Option calls below:<br>
      </p>
      {output}
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

IST = pytz.timezone('Asia/Kolkata')

def is_market_hours():
    now_ist = datetime.now(IST).time()
    return dt_time(9, 15) <= now_ist <= dt_time(14, 45)
  
chk = []
while True:
    now_ist = datetime.now(IST).time()
    if is_market_hours():
        try:
            list_ = {'^NSEI':"Nifty 50",'^NSEBANK':"BankNifty",'NIFTY_FIN_SERVICE.NS':"FinNifty",'^BSESN':"SENSEX"}
            dff= []
            
            for i in list_:
                df = index_5min_breakout(i,'1d')[['Datetime','Close','breakout_down']]
                df['index'] = list_[i]
                dff.append(df)
            breakout = pd.concat(dff)
            breakout= breakout.sort_values(by=['Datetime'])
            breakout = breakout[~breakout['Datetime'].isin(chk)]
            if breakout.empty :
              print("No new breakout")
            else:
              chk.extend(breakout['Datetime'])
            if len(breakout) == 0:
                output = "<h1>No Breakout or Breakdown till now</h1>"  # HTML for the message
            else:
                output = build_table(breakout, 'yellow_dark', font_size='small', font_family='Open Sans, sans-serif',
                                    text_align='center', width='Auto', index=False, even_color='black', even_bg_color='white')

            if len(breakout) > 0:
                send_mail(output)
            else: 
               pass
        except Exception as e:
            print(f"Error occurred: {e}")
    else:
        break
    time.sleep(60)
            


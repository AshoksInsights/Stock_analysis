from fyers_apiv3 import fyersModel
import pandas as pd
from fyers_apiv3.FyersWebsocket import data_ws
import datetime as dt
import time 
import numpy as np
import math
import json
import pyotp
from urllib import parse
import sys
from datetime import datetime, timedelta
import pandas_ta as ta
import matplotlib.pyplot as plt
import requests


FY_ID = "YJ08526"
APP_ID_TYPE = "2"
TOTP_KEY = "W3UOSVQQO2V4KJT3RRXYJDHFBKP3372N"
PIN = "7776"
APP_ID = "ETYHMVN1Q6"
REDIRECT_URI = "https://www.google.com/"
APP_TYPE = "100"
APP_ID_HASH = 'dc1cd1f989e67ad53623c26ac48315e1e88ed60bdd58a2cbc12ea294c248d3db'
response_type = "code"
grant_type = "authorization_code"

BASE_URL = "https://api-t2.fyers.in/vagator/v2"
BASE_URL_2 = "https://api-t1.fyers.in/api/v3"
# BASE_URL_2 = "https://api.fyers.in/api/v2/"
URL_SEND_LOGIN_OTP = BASE_URL + "/send_login_otp"
URL_VERIFY_TOTP = BASE_URL + "/verify_otp"
URL_VERIFY_PIN = BASE_URL + "/verify_pin"
URL_TOKEN = BASE_URL_2 + "/token"
URL_VALIDATE_AUTH_CODE = BASE_URL_2 + "/validate-authcode"

SUCCESS = 1
ERROR = -1
def verify_client_id(CLIENT_ID,app_id):
    try:
        payload = {
            "fy_id": CLIENT_ID,
            "app_id": app_id
        }

        result_string = requests.post(url=URL_SEND_LOGIN_OTP, json=payload)
        # print("result_string : ", result_string.text)
        if result_string.status_code != 200:
            return [ERROR, result_string.text]

        result = json.loads(result_string.text)
        request_key = result["request_key"]

        return [SUCCESS, request_key]
    
    except Exception as e:
        return [ERROR, e]
def generate_totp(TOTP_KEY):
    try:
        generated_totp = pyotp.TOTP(TOTP_KEY).now()
        return [SUCCESS, generated_totp]
    
    except Exception as e:
        return [ERROR, e]
def verify_totp(request_key, totp):
    try:
        payload = {
            "request_key": request_key,
            "otp": totp
        }

        result_string = requests.post(url=URL_VERIFY_TOTP, json=payload)
        if result_string.status_code != 200:
            return [ERROR, result_string.text]

        result = json.loads(result_string.text)
        request_key = result["request_key"]

        return [SUCCESS, request_key]
    
    except Exception as e:
        return [ERROR, e]
def verify_PIN(request_key, pin):
    try:
        payload = {
            "request_key": request_key,
            "identity_type": "pin",
            "identifier": pin
        }

        result_string = requests.post(url=URL_VERIFY_PIN, json=payload)
        if result_string.status_code != 200:
            return [ERROR, result_string.text]
    
        result = json.loads(result_string.text)
        access_token = result["data"]["access_token"]

        return [SUCCESS, access_token]
    
    except Exception as e:
        return [ERROR, e]

def token(fy_id, app_id, redirect_uri, app_type, access_token):
    try:
        payload = {
            "fyers_id": fy_id,
            "app_id": app_id,
            "redirect_uri": redirect_uri,
            "appType": app_type,
            "code_challenge": "",
            "state": "sample_state",
            "scope": "",
            "nonce": "",
            "response_type": "code",
            "create_cookie": True
        }
        headers={'Authorization': f'Bearer {access_token}'}

        result_string = requests.post(
            url=URL_TOKEN, json=payload, headers=headers
        )

        if result_string.status_code != 308:
            return [ERROR, result_string.text]

        result = json.loads(result_string.text)
        url = result["Url"]
        auth_code = parse.parse_qs(parse.urlparse(url).query)['auth_code'][0]

        return [SUCCESS, auth_code]
    
    except Exception as e:
        return [ERROR, e]
def validate_authcode(auth_code):
    try:
        payload = {
            "grant_type": "authorization_code",
            "appIdHash": APP_ID_HASH,
            "code": auth_code,
        }

        result_string = requests.post(url=URL_VALIDATE_AUTH_CODE, json=payload)
        if result_string.status_code != 200:
            return [ERROR, result_string.text]

        result = json.loads(result_string.text)
        access_token = result["access_token"]

        return [SUCCESS, access_token]
    
    except Exception as e:
        return [ERROR, e]
def main():
    # Step 1 - Retrieve request_key from verify_client_id Function
    verify_client_id_result = verify_client_id(FY_ID,APP_ID)
    if verify_client_id_result[0] != SUCCESS:
        print(f"verify_client_id failure - {verify_client_id_result[1]}")
        sys.exit()
    else:
        print("verify_client_id success")

    # Step 2 - Generate totp
    generate_totp_result = generate_totp(TOTP_KEY)
    if generate_totp_result[0] != SUCCESS:
        print(f"generate_totp failure - {generate_totp_result[1]}")
        sys.exit()
    else:
        print("generate_totp success")

    # Step 3 - Verify totp and get request key from verify_totp Function.
    request_key = verify_client_id_result[1]
    totp = generate_totp_result[1]
    verify_totp_result = verify_totp(request_key=request_key, totp=totp)
    if verify_totp_result[0] != SUCCESS:
        print(f"verify_totp_result failure - {verify_totp_result}")
        sys.exit()
    else:
        print("verify_totp_result success")

    # Step 4 - Verify pin and send back access token
    request_key_2 = verify_totp_result[1]
    verify_pin_result = verify_PIN(request_key=request_key_2, pin=PIN)
    if verify_pin_result[0] != SUCCESS:
        print(f"verify_pin_result failure - {verify_pin_result[1]}")
        sys.exit()
    else:
        print("verify_pin_result success")

    # Step 5 - Get auth code for API V3 App from trade access token
    token_result = token(
        fy_id=FY_ID, app_id=APP_ID, redirect_uri=REDIRECT_URI, app_type=APP_TYPE,
        access_token=verify_pin_result[1]
    )
    if token_result[0] != SUCCESS:
        print(f"token_result failure - {token_result[1]}")
        sys.exit()
    else:
        print("token_result success")

    # Step 6 - Get API V3 access token from validating auth code
    auth_code = token_result[1]
    validate_authcode_result = validate_authcode(auth_code=auth_code)
    if token_result[0] != SUCCESS:
        print(f"validate_authcode failure - {validate_authcode_result[1]}")
        sys.exit()
    else:
        print("validate_authcode success")
    
    access_token = APP_ID + "-" + APP_TYPE + ":" + validate_authcode_result[1]

    print(f"\naccess_token - {access_token}\n")

    return access_token


access_token = main()
data = {"access_token": access_token}
with open('access_token.json', 'w') as json_file:
    json.dump(data, json_file)




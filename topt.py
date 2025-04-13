import pyotp as tp
totp_key = 'W3UOSVQQO2V4KJT3RRXYJDHFBKP3372N'
totp = tp.TOTP(totp_key).now()
print(totp)


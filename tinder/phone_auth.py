import aiohttp
import requests
import json

from tinder.api import TinderAPI

# from fill_databases.Customers.tokens import fill

CODE_REQUEST_URL = "https://api.gotinder.com/v2/auth/sms/send?auth_type=sms"
CODE_VALIDATE_URL = "https://api.gotinder.com/v2/auth/sms/validate?auth_type=sms"
TOKEN_URL = "https://api.gotinder.com/v2/auth/login/sms"

HEADERS = {'photos-agent': 'Tinder/11.4.0 (iPhone; iOS 12.4.1; Scale/2.00)', 'content-type': 'application/json'}


# def send_sms_code(phone_number):
#     data = {'phone_number': phone_number}
#     r = requests.post(CODE_REQUEST_URL, headers=HEADERS, data=json.dumps(data), verify=False)
#     print(r)
#     print(r.url)
#     response = r.json()
#     print(response)
#     if (response.get("data")['sms_sent'] == False):
#         return False
#     return True


# def send_sms_code(phone: str) -> dict:
#     # TODO: Make the function asynchronous import aiohttp, import asyncio
#     """
#
#     :type phone: object
#     """
#     data = {'phone_number': phone}
#     # Q:
#     #  'verify=False' what is mean ?
#     response = requests.post(CODE_REQUEST_URL, headers=HEADERS, data=json.dumps(data), verify=False).json()
#     # print(response)
#     # test_response = {'meta': {'status': 200}, 'data': {'otp_length': 6, 'sms_sent': True}}
#     # TODO: logging
#     # Q:
#     #  How to sey client (and remind to them) that they send a lot of request, and they should wait? send after? (where is limit?)
#     # Q: how many time the code will be fresh?
#     return response


async def send_sms_code(phone: str) -> dict:
    data = {'phone_number': phone}
    async with aiohttp.ClientSession() as session:
        # async with session.post(CODE_REQUEST_URL, headers=HEADERS, json=data, ssl=False) as response:
        #     return await response.json()
        return {'meta': {'status': 200}, 'data': {'otp_length': 6, 'sms_sent': True}}
        # return {'meta': {'status': 403}, 'error': {'code': 40316}}


async def get_tinder_token(sms_code: int, phone_number: str) -> dict:
    # Q:
    #  what will be If exclude <phone_number> ?
    # otp_code: one-time password code
    data = {'otp_code': sms_code, 'phone_number': phone_number}
    async with aiohttp.ClientSession() as session:
        # async with requests.post(CODE_VALIDATE_URL, headers=HEADERS, json=data, verify=False) as response:
        #     return await response.json()
        # TODO: logging
        return {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'validated': True}}
        # return {'meta': {'status': 400}, 'error': {'code': 41201, 'message': 'Invalid OTP token'}}

async def get_api_token(refresh_token: str) -> dict:
    data = {'refresh_token': refresh_token}
    async with aiohttp.ClientSession() as session:
        # async with requests.post(TOKEN_URL, headers=HEADERS, data=json.dumps(data), verify=False) as response:
        #     return await response.json()
    # TODO: logging
    #     return {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'onboarding_token': '72e76186-6795-40b7-a382-9533fa21bc06', 'is_new_user': True}}
        return {'meta': {'status': 200}, 'data': {'_id': '60bde6448fb9ce01006897a0', 'api_token': 'da004c39-7813-42de-8dd3-6ab7e2b2b487', 'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'is_new_user': False}}
    #     return {'meta': {'status': 401}, 'error': {'code': 40120}}


if __name__ == '__main__':
    # x_auth_token = '33770071-0d84-4817-a5e5-be54839b5f99'
    x_auth_token = '33770071-0d84-4817-a5e5-be54839b5f99'
    print(TinderAPI(x_auth_token).profile())
    # phone_number = input("Please enter your phone number under the international format (country code + number): ")
    # phone_number = '+79259261386'
    # phone_number = '+79163546695'
    # log_code = send_sms_code(phone_number)
    # print(log_code)
    # otp_code = input("Please enter the code you've received by sms: ")
    # refresh_token = get_tinder_token(otp_code, phone_number)
    # refresh_token = input("Please enter your refresh_token: ")
    # refresh_token = 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU'
    # refresh_token = None
    # x_auth_token = get_api_token(refresh_token)
    # print(x_auth_token)
#     # print(f'log_code: {log_code}')
#     # print(f'refresh_token: {refresh_token}')
#     X_Auth_Token = str(get_api_token(refresh_token))
#     print("Here is your Tinder token: " + X_Auth_Token)
# #
# fill(X_Auth_Token)  # fill tokens table if it is unique


# 89256488052: {'meta': {'status': 403}, 'error': {'code': 40316}}
# +79256488052: {'meta': {'status': 200}, 'data': {'otp_length': 6, 'sms_sent': True}}
# after one minute
# +79256488052: {'meta': {'status': 429}, 'error': {'code': 41205, 'message': 'Failed rate limiter check'}}
#
# right sms_code:
# {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'validated': True}}
# {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'validated': True}}
# expired sms_code (twice inputting): {'meta': {'status': 400}, 'error': {'code': 41201, 'message': 'Invalid OTP token'}}
# wrong_code: {'meta': {'status': 400}, 'error': {'code': 41201, 'message': 'Invalid OTP token'}}

# refresh_token
# (!) new user (not registered):
# {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'onboarding_token': '72e76186-6795-40b7-a382-9533fa21bc06', 'is_new_user': True}}
# old user:
# {'meta': {'status': 200}, 'data': {'_id': '60bde6448fb9ce01006897a0', 'api_token': 'da004c39-7813-42de-8dd3-6ab7e2b2b487', 'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'is_new_user': False}}
# wrong refresh_token:
# {'meta': {'status': 401}, 'error': {'code': 40120}}

# get_api_token -- x_auth_token
#  wrong 'refresh_token': {'meta': {'status': 401}, 'error': {'code': 40120}}
# right 'refresh_token': {'meta': {'status': 200}, 'data': {'_id': '60bde6448fb9ce01006897a0', 'api_token': '33770071-0d84-4817-a5e5-be54839b5f99', 'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'is_new_user': False}}


# TinderAPI(x_auth_token):
# wrong:

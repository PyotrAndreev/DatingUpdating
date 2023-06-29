import copy


def add_suffix_to_keys(dictionary: dict, prefix: str) -> dict:
    new_dictionary = {}
    for key, value in dictionary.items():
        if key != '_id':  # _id is tinder_id, it shouldn't be in the last_info, should be in the account table
            # the next condition for 'error_code', 'meta_status', 'message' and another unknown
            if key not in ['refresh_token', 'onboarding_token', 'is_new_user', 'api_token', 'validated', 'otp_length',
                           'sms_sent']:
                key = f'{prefix}|{key}'
            new_dictionary[key] = value
    return new_dictionary


def prepare_data_to_db(response: dict, prefix: str) -> dict:
    meta_data = copy.deepcopy(response.get('meta', {}))
    if meta_data:
        meta_data['meta_status'] = meta_data.pop('status')

    if meta_data.get('meta_status') == 200:
        data: dict = copy.deepcopy(response.get('data', {}))
    else:
        data: dict = copy.deepcopy(response.get('error', {}))  # error_data
        data['error_code'] = data.pop('code')

    return add_suffix_to_keys({**meta_data, **data}, prefix)


if __name__ == '__main__':
    responses = [{'meta': {'status': 403}, 'error': {'code': 40316}},
                 {'meta': {'status': 200}, 'data': {'otp_length': 6, 'sms_sent': True}},
                 {'meta': {'status': 429}, 'error': {'code': 41205, 'message': 'Failed rate limiter check'}},
                 {'meta': {'status': 400}, 'error': {'code': 41201, 'message': 'Invalid OTP token'}},
                 {'meta': {'status': 400}, 'error': {'code': 41201, 'message': 'Invalid OTP token'}},
                 {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'onboarding_token': '72e76186-6795-40b7-a382-9533fa21bc06', 'is_new_user': True}},
                 {'meta': {'status': 200}, 'data': {'_id': '60bde6448fb9ce01006897a0', 'api_token': 'da004c39-7813-42de-8dd3-6ab7e2b2b487', 'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'is_new_user': False}},
                 {'meta': {'status': 401}, 'error': {'code': 40120}},
                 {'meta': {'status': 200}, 'data': {'_id': '60bde6448fb9ce01006897a0', 'api_token': '33770071-0d84-4817-a5e5-be54839b5f99', 'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTkyNjEzODY.5g6F-eWqAT8c8DnaCvibCbG7DnLTYECN0EtfnxLajeU', 'is_new_user': False}},
                 {'meta': {'status': 200}, 'data': {'refresh_token': 'eyJhbGciOiJIUzI1NiJ9.NzkyNTY0ODgwNTI.brsaoJImNU5WJsmblav-cj0GDypVBJud_a3owrSM1mA', 'validated': True}}]

    for resp in responses:
        print(prepare_data_to_db(resp, prefix='refresh_token'))

import re
import phonenumbers

from tg_bot.data_structure import users


def del_not_digits(phone_number: str) -> str:
    """Remove all non-digit characters from a phone number."""
    return re.sub(r'\D', '', phone_number)


def right_phone_number(phone_number: str) -> str or False:
    """
        Validate and normalize a phone number string.

        :type phone_number: object
        :return str or False:
        The normalized phone number string with country code, or False if the phone number is invalid.
    """
    phone_number = '+' + del_not_digits(phone_number)
    # TODO: send customer message in every return
    try:
        parsed_number = phonenumbers.parse(phone_number)
        if phonenumbers.is_valid_number(parsed_number):
            # TODO: logging
            region_code = phonenumbers.region_code_for_number(parsed_number)
            if region_code == 'None':
                # TODO: logging (Region not defined)
                return False
            return phonenumbers.region_code_for_number(parsed_number)
            # TODO: logging
        else:
            # TODO: logging (not valid phone number)
            return False
    except phonenumbers.NumberParseException:
        # TODO: logging (phone_number wasn't parsed)
        return False


def right_sms_code(user_id: int, sms_code: str) -> False:
    sms_code = del_not_digits(sms_code)
    if len(sms_code) != users[user_id].DBUser.len_sms_code:
        # TODO: logging
        return False
    return True
    # return True
    # else:
    #     if
    #
    #     return True
    # except:
    #     # TODO: logging (not right code 'validated is False')
    #     return False
    #     pass


if __name__ == '__main__':
    # print(right_phone_number('+++7---(925) - R(G3))))((((()4926  hjk1386'))
    print(right_phone_number('+89259261386'))
    # phone_number = '+79259261386'
    # parsed_number = phonenumbers.parse(phone_number)
    # # print(len(parsed_number))
    # print(phonenumbers.is_valid_number(parsed_number))

import unittest

from Utils.util_basic import lookup_user_address, verify_user_address


class TestUtils(unittest.TestCase):
    def test_verify_address(self):
        line_1 = 'random street in raleigh'
        line_2 = ''
        city = 'raleigh'
        state = 'nc'
        zip_code = ''
        response = lookup_user_address(line_1, line_2, city, state, zip_code)
        print(response.text)
        verify_user_address(line_1, line_2, city, state, zip_code)
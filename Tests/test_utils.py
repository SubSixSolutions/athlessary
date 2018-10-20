import unittest

from Utils.util_basic import lookup_user_address, verify_user_address


class TestUtils(unittest.TestCase):
    def test_verify_address(self):
        line_1 = '29 east green street'
        line_2 = ''
        city = 'Champaign'
        state = 'Illinois'
        zip_code = ''
        response = lookup_user_address(line_1, line_2, city, state, zip_code)
        print(response.text)
        verify_user_address(line_1, line_2, city, state, zip_code)

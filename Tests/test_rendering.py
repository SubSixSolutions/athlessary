import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

from Utils.data_loading import csv_to_db
from Utils.db import Database
from Utils.log import log
from Utils.config import db
import time
from Utils.config import db


def clean_up_table(table, pk):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestBasicRender(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        clean_up_table('users', 'user_id')
        cls.create_test_user()

    @classmethod
    def create_test_user(cls):
        driver = webdriver.Firefox()
        driver.get("http://127.0.0.1:5000/")
        sign_up = driver.find_element_by_link_text('Sign Up')
        sign_up.click()
        username = driver.find_element_by_id('username')
        first = driver.find_element_by_id('first')
        last = driver.find_element_by_id('last')
        password = driver.find_element_by_id('password')
        password_confirm = driver.find_element_by_id('retype_pass')
        submit = driver.find_element_by_id('submit')
        username.send_keys('test_user')
        first.send_keys('w')
        last.send_keys('k')
        password.send_keys('123')
        password_confirm.send_keys('123')
        submit.click()
        log_out = driver.find_element_by_link_text('Log Out')
        log_out.click()
        driver.close()

    def setUp(self):
        self.driver = webdriver.Firefox()

    def tearDown(self):
        self.driver.close()

    def test_home_title(self):
        self.driver.get("http://127.0.0.1:5000/")
        title = self.driver.title
        self.assertEqual("Athlessary", title)

    def test_sign_up(self):
        self.driver.get("http://127.0.0.1:5000/")
        sign_up = self.driver.find_element_by_link_text('Sign Up')
        sign_up.click()
        username = self.driver.find_element_by_id('username')
        first = self.driver.find_element_by_id('first')
        last = self.driver.find_element_by_id('last')
        password = self.driver.find_element_by_id('password')
        password_confirm = self.driver.find_element_by_id('retype_pass')
        submit = self.driver.find_element_by_id('submit')
        username.send_keys('test_user2')
        first.send_keys('w1')
        last.send_keys('k1')
        password.send_keys('123')
        password_confirm.send_keys('123')
        submit.click()
        title = self.driver.title
        log_out = self.driver.find_element_by_link_text('Log Out')
        log_out.click()
        self.assertEqual("w1 k1", title)

    def login(self, u, p):
        self.driver.get("http://127.0.0.1:5000/")
        username = self.driver.find_element_by_id('username_field')
        password = self.driver.find_element_by_id('password_field')
        sign_in = self.driver.find_element_by_id('submit_bttn')
        username.send_keys(u)
        password.send_keys(p)
        sign_in.click()

    def test_login(self):
        self.login('test_user', '123')
        title = self.driver.title
        self.assertEqual("w k", title)

    def test_logout(self):
        self.login('test_user', '123')
        log_out = self.driver.find_element_by_link_text('Log Out')
        log_out.click()
        title = self.driver.title
        self.assertEqual("Athlessary", title)

    def test_roster(self):
        self.login('test_user', '123')
        self.driver.get("http://127.0.0.1:5000/roster")
        title = self.driver.title
        self.assertEqual("Roster", title)

    def test_profile(self):
        self.login('test_user', '123')
        self.driver.get("http://127.0.0.1:5000/profile")
        bio = self.driver.find_element_by_id('bio')
        self.assertEqual("Hi, my name is w!", bio.text)
        address = self.driver.find_element_by_id('address')
        self.assertEqual('123 East Main Street', address.get_attribute('placeholder'))

    def test_roster_contents(self):
        self.login('test_user', '123')
        self.driver.get("http://127.0.0.1:5000/roster")
        table = self.driver.find_element_by_id('athlete_table')
        rows = table.find_elements(By.TAG_NAME, "tr")
        for row in rows:
            self.assertEqual("Name Address Number of Seats Driving?", row.text)

import unittest

from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.support.ui import WebDriverWait # available since 2.4.0
from selenium.webdriver.support import expected_conditions as EC # available since 2.26.0

from Utils.data_loading import csv_to_db
from Utils.db import Database
from Utils.log import log
from Utils.config import db

from Utils.config import db


def clean_up_table(table, pk):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestRosterPage(unittest.TestCase):
    # def setUp(self):
    #     path = 'TestResources/roster_test_data.csv'
    #     csv_to_db(path)

    def test_home_title(self):
        driver = webdriver.Firefox()
        driver.get("http://127.0.0.1:5000/")
        title = driver.title
        self.assertEqual("Athlessary", title)
        driver.close()
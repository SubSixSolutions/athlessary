import unittest

from Utils.data_loading import csv_to_db
from Utils.db import Database
from Utils.driver_generation import generate_cars, modified_k_means
from Utils.log import log
from Utils.config import db

from Utils.config import db


def clean_up_table(table, pk):
    # empty users
    rows = db.select(table, [pk], fetchone=False)
    for _id in rows:
        db.delete_entry(table, pk, _id[pk])


class TestDriverGeneration(unittest.TestCase):
    def setUp(self):
        path = 'TestResources/dg_test_data.csv'
        csv_to_db(path)

    def test_easy_generation(self):
        result = db.select('users', ['ALL'], fetchone=False)
        athletes = []
        drivers = []
        for user in result:
            log.info(user['num_seats'])
            if user['num_seats'] > 0:
                drivers.append(user['user_id'])
            else:
                athletes.append(user['user_id'])

        log.debug("Drivers: {}".format(drivers))
        log.debug("Athletes: {}".format(athletes))
        drivers_arr, athlete_dict = generate_cars(athletes, drivers)
        log.debug("Drivers: {}".format(drivers_arr))
        log.debug("Athletes: {}".format(athlete_dict))
        modified_k_means(drivers_arr, athlete_dict)


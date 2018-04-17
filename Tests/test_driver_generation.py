import unittest

import numpy as np

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
    @classmethod
    def setUpClass(cls=None):
        clean_up_table('users', 'user_id')

    def setUp(self):
        path = 'TestResources/dg_test_data.csv'
        result = db.select('users', ['ALL'], fetchone=False)

        if len(result) == 0:
            csv_to_db(path)
            result = db.select('users', ['ALL'], fetchone=False)

        self.athletes = []
        self.drivers = []
        for user in result:
            if user['num_seats'] > 0:
                self.drivers.append(user['user_id'])
            else:
                self.athletes.append(user['user_id'])

    def test_easy_generation(self):
        expected_assignments = {self.drivers[0]: [self.athletes[0]]}
        drivers_arr, athlete_dict = generate_cars(self.athletes[0:1], self.drivers[0:1])

        drivers = modified_k_means(drivers_arr, athlete_dict)

        assignments = {}
        for driver_id in list(drivers.keys()):
            driver = drivers[driver_id]
            curr_driver_athletes = driver['athletes']
            curr_driver_athletes = np.array(curr_driver_athletes)
            curr_driver_athletes = curr_driver_athletes[:, 0]
            assignments[driver_id] = list(curr_driver_athletes)

        self.assertAlmostEqual(assignments, expected_assignments)

    def test_not_enough_drivers(self):
        car_data = generate_cars(self.athletes, [])
        self.assertIsNone(car_data)

    def test_generate_all(self):
        drivers_arr, athlete_dict = generate_cars(self.athletes, self.drivers)
        drivers = modified_k_means(drivers_arr, athlete_dict)

        assignments = {}
        for driver_id in list(drivers.keys()):
            driver = drivers[driver_id]
            curr_driver_athletes = driver['athletes']
            if len(curr_driver_athletes) > 0:
                curr_driver_athletes = np.array(curr_driver_athletes)
                curr_driver_athletes = curr_driver_athletes[:, 0]
                assignments[driver_id] = list(curr_driver_athletes)

        log.debug(assignments)
        # self.assertAlmostEqual(assignments, expected_assignments)

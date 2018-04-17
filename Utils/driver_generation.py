import math

import numpy as np

from Utils.config import db
from Utils.log import log


def generate_cars(athletes, drivers):
    """
    given an array of user_ids (separated into athletes and drivers),
    build a data structure with the ids, and coordinates of their location
    :param athletes: array of user_ids
    :param drivers: array of user_ids of people driving
    :return: dictionary of drivers; dictionary of athletes
    """

    # get results from database
    results = db.select('users', select_cols=['ALL'], where_cols=['user_id'],
                        where_params=[athletes + drivers], fetchone=False)

    total_seats = 0

    # initialize data structures
    driver_dict = {}
    athlete_dict = {}

    # loop through users and build driver and athlete data structures
    for user in results:
        curr_id = user['user_id']
        num_seats = user['num_seats']
        info_dict = {'x': user['x'], 'y': user['y'], 'id': curr_id, 'num_seats': 0}
        if curr_id in drivers:
            info_dict['num_seats'] = num_seats
            info_dict['num_assigned'] = 0
            info_dict['athletes'] = []
            driver_dict[curr_id] = info_dict
            total_seats += num_seats
        else:
            athlete_dict[curr_id] = info_dict

    if total_seats < len(athletes):
        return None
    else:
        return driver_dict, athlete_dict


def find_squared_distance(x1, y1, x2, y2):
    """
    given 2 points, find the euclidean distance between them
    :param x1:
    :param y1:
    :param x2:
    :param y2:
    :return: the euclidean distance
    """

    y_diff = y1 - y2
    x_diff = x1 - x2
    x_sqr = math.pow(x_diff, 2)
    y_sqr = math.pow(y_diff, 2)
    dist = math.sqrt(x_sqr + y_sqr)

    return dist


def init_distance_matrix(drivers, athletes):
    """
    will create a dictionary of arrays; each athlete id is the key for
    an array that holds the id and distance of each driver
    i.e { athlete_1 : [ [driver_2 : .038383], [driver_3 : .084748] ], ... }
    :param drivers: dictionary of drivers
    :param athletes: dictionary of athletes
    :return: dictionary of athlete ids as keys and distances as data

    """

    distance_matrix = {}
    for key, athlete in athletes.items():

        # athlete coordinates
        athlete_x = athlete['x']
        athlete_y = athlete['y']
        dist_arr = []

        # find squared distance from each driver
        for driver_id, driver in drivers.items():
            # find distance between points
            dist = find_squared_distance(athlete_x, athlete_y, driver['x'], driver['y'])

            # build and append dist_entry to current athletes distance array
            dist_entry = [driver['id'], dist]
            dist_arr.append(dist_entry)

        # add the distance array to the data structure; the key is the athlete id for easy lookup
        distance_matrix[athlete['id']] = np.asarray(dist_arr)
    return distance_matrix


def assign_to_cars(drivers, athletes, data):
    """
    assigns athletes to cars given data about the distance of each athlete
    from each car
    :param drivers: dictionary of drivers
    :param athletes: dictionary of athletes
    :param data: a dictionary keyed by the athlete id
    :return: the driver dictionary; modified to reflect the current athlete assignments

    """
    # take values from athlete dictionary and iterate over them
    athletes = list(athletes.values())
    seen_athletes = {}

    while len(athletes) > 0:
        # remove athlete from the queue
        athlete = athletes.pop()
        seen_athletes[athlete['id']] = athlete

        # look up the athlete's distance array from the data parameter
        dist_arr = data[athlete['id']]

        # find the smallest distance and the id of the driver that is the smallest distance from the athlete
        smallest_dist, smallest_dist_id = get_car_assignments(drivers, dist_arr)

        if smallest_dist is not None:
            curr_driver = drivers[smallest_dist_id]
            curr_driver_athletes = curr_driver['athletes']
            if len(curr_driver_athletes) > 0:
                curr_driver_athletes = np.array(curr_driver_athletes)
                curr_driver_athletes = curr_driver_athletes[:,0]
            if athlete['id'] in curr_driver_athletes:
                continue
            elif curr_driver['num_assigned'] < curr_driver['num_seats']:
                # add athlete to the current driver
                curr_driver['athletes'].append([athlete['id'], smallest_dist])
            else:
                # Get the index of the furthest athlete that the driver has in his/her car
                furthest_athlete_idx = np.argmax(curr_driver['athletes'], axis=0)[1]
                furthest_athlete_id = curr_driver['athletes'][furthest_athlete_idx][0]
                # put furthest athlete back on queue
                if seen_athletes.get(furthest_athlete_id):
                    athletes.append(seen_athletes[furthest_athlete_id])

                # update the driver by replacing an athlete
                curr_driver['athletes'][furthest_athlete_idx] = [athlete['id'], smallest_dist]
            curr_driver['num_assigned'] += 1
    return drivers


def get_car_assignments(drivers, distances):
    """
    takes an array of distances representing one athlete's distance from
    every driver and selects an appropriate driver
    :param drivers: dictionary of drivers
    :param distances: an array of distances for the given athlete
    :return: the smallest distance and the id of the driver

    """

    smallest_driver = None
    smallest_dist = 0

    # loop through all the drivers (all of the distances in the athlete distance array)
    for dist in distances:
        driver_id = dist[0]
        distance = dist[1]
        curr_driver = drivers[driver_id]
        if (curr_driver['num_assigned'] < curr_driver['num_seats']) or should_replace_athlete(curr_driver, distance):
            if not smallest_driver or distance < smallest_dist:
                smallest_driver = driver_id
                smallest_dist = distance

    if smallest_driver is not None:
        return smallest_dist, smallest_driver
    else:
        return None, None


def should_replace_athlete(driver, distance):
    """
    determines whether an athlete should be removed from the
    car in favor of this new athlete
    :param driver: the current driver dictionary
    :param distance: a float representing the distance between the current driver and
    some athlete in question
    :return: True or False; True if the distance is less than any of the athletes currently in the
    driver's car; False otherwise

    """

    for athlete in driver['athletes']:
        dist = athlete[1]
        if dist > distance:
            # TODO return ID?
            return True
    return False


def update_drivers(driver_dict, athletes):
    """
    update the address of all the drivers based on the athletes
    they are supposed to be picking up
    :param driver_dict: dictionary data structure containing all of the drivers
    :param athletes: athlete dictionary data structure; keyed by athlete id. Needed to find the average of all
    the athletes in a driver's car
    :return: True or False; True if the driver locations (centroids) have not moved; False otherwise

    """

    is_complete = True

    for driver_id, driver in driver_dict.items():
        if driver['num_assigned'] > 1:
            # average athlete positions
            sum_x = 0
            sum_y = 0
            for athlete in driver['athletes']:
                curr_athlete = athletes[athlete[0]]
                sum_x += curr_athlete['x']
                sum_y += curr_athlete['y']
            new_x = sum_x / float(driver['num_assigned'])
            new_y = sum_y / float(driver['num_assigned'])

            bounce = False
            old_x = driver.get('old_x')
            old_y = driver.get('old_y')
            if old_x and old_y:
                if np.isclose(old_x, new_x) and np.isclose(old_y, new_y):
                    bounce = True
            # update the driver x and y to be the average if x and y have changed
            if not bounce and (driver['x'] != new_x or driver['y'] != new_y):
                log.debug('driver: {}'.format(driver['id']))
                log.debug('old_x: {} x: {} -> {}'.format(old_x, driver['x'], new_x))
                log.debug('old_y: {} y: {} -> {}'.format(old_y, driver['y'], new_y))
                driver['old_x'] = driver['x']
                driver['old_y'] = driver['y']
                driver['x'] = new_x
                driver['y'] = new_y
                is_complete = False
                driver['athletes'] = []
                driver['num_assigned'] = 0

    return is_complete


def modified_k_means(drivers, athletes):
    """
    :param drivers:
    :param athletes:
    :return:
    """

    data = init_distance_matrix(drivers, athletes)

    # assign athletes to cars
    assign_to_cars(drivers, athletes, data)

    # update centroids based on new grouping
    is_complete = update_drivers(drivers, athletes)

    # move centroids until old and new match
    while not is_complete:

        # get distance matrix
        distances = init_distance_matrix(drivers, athletes)

        # assign athletes to cars
        assign_to_cars(drivers, athletes, distances)

        # update centroids based on new grouping
        is_complete = update_drivers(drivers, athletes)

    log.info('Successfully assigned athletes to cars as follows: {}'.format(drivers))
    return drivers

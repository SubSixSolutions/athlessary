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
        if str(curr_id) in drivers:
            info_dict['num_seats'] = num_seats
            info_dict['num_assigned'] = 0
            info_dict['athletes'] = []
            driver_dict[curr_id] = info_dict
            total_seats += num_seats
        else:
            athlete_dict[curr_id] = info_dict

    print(driver_dict)
    print(athlete_dict)

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
            if curr_driver['num_assigned'] < curr_driver['num_seats']:
                # add athlete to the current driver
                curr_driver['athletes'].append([athlete['id'], smallest_dist])
            else:
                furthest_athlete_idx = np.argmax(curr_driver['athletes'], axis=0)[1]
                furthest_athlete_id = curr_driver['athletes'][furthest_athlete_idx][0]

                # put furthest athlete back on queue
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
    :return: True or False; True if the disance is less than any of the athletes currently in the
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

            # update the driver x and y to be the average if x and y have changed
            if driver['x'] != new_x or driver['y'] != new_y:
                driver['x'] = new_x
                driver['y'] = new_y
                is_complete = False
                driver['athletes'] = []
                driver['num_assigned'] = 0

    return is_complete


# def check_efficiency(drivers, distances):
#     """
#     takes in the drivers after they have been assigned and see
#     if a car can be reduced
#     :param drivers: array of drivers
#     :param distances: array of distances
#     :return:
#     """
#
#     empty_seats = 0
#     least_used_car = None
#     len_athletes = 0
#     for driver in drivers:
#         if least_used_car is None:
#             least_used_car = driver
#         empty_seats += (driver.car_size - len(driver.points))
#         if (driver.car_size - len(driver.points)) > (least_used_car.car_size - len(least_used_car.points)):
#             least_used_car = driver
#         driver.prev_address = ""
#         len_athletes +=  len(driver.points)
#     if (len(least_used_car.points) + 1) <= (empty_seats - (least_used_car.car_size - len(least_used_car.points))):
#         print "Removing driver " + least_used_car.driver_name + " to improve efficiency..."
#         remove_driver(drivers, least_used_car, distances)
#         return True
#     return False
#
#
# def remove_driver(drivers, driver_to_remove, data):
#     """
#     takes in a list of drivers and a specific driver to convert
#     into an athlete
#     :param drivers: list of drivers
#     :param driver_to_remove: driver being removed
#     :param data: data array of distances
#     :return:
#     """
#
#     athlete_arr = []
#     for athlete in driver_to_remove.points:
#         athlete_arr.append(athlete)
#     new_athlete = Athlete(driver_to_remove.driver_name, driver_to_remove.driver_address, len(data), driver_to_remove.dorm_code)
#     drivers.remove(driver_to_remove)
#     athlete_arr.append(new_athlete)
#     data = add_row_to_data(drivers, new_athlete, data)
#     modified_k_means(drivers, athlete_arr, data)


def modified_k_means(drivers, athletes):
    """
    :param drivers:
    :param athletes:
    :return:
    """
    print("Running KMeans with added Athletes...")
    print(drivers, athletes)

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

    print('final result')
    log.info(drivers)

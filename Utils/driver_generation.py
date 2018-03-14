import math

import numpy as np

from Utils.log import log


def generate_cars(athletes, drivers, db):
    results = db.select('users', select_cols=['ALL'], where_cols=['id'],
                        where_params=[athletes + drivers], fetchone=False)

    total_seats = 0

    driver_dict = {}
    athlete_arr = []
    for user in results:
        curr_id = user['id']
        num_seats = user['num_seats']
        info_dict = {'x': user['x'], 'y': user['y'], 'id': curr_id, 'num_seats': 0}
        if str(curr_id) in drivers:
            info_dict['num_seats'] = num_seats
            info_dict['num_assigned'] = 0
            info_dict['athletes'] = []
            driver_dict[curr_id] = info_dict
            total_seats += num_seats
        else:
            athlete_arr.append(info_dict)

    print(driver_dict)
    print(athlete_arr)

    return driver_dict, athlete_arr


def init_distance_matrix(drivers, athletes):
    """
    will create an array of arrays... each inner array represents the
    athlete's distance from the driver with that ID
    :param drivers: array of driver Objects
    :param athletes: array of athlete Objects
    :return: 2D array of distances

    DONE

    """
    print(athletes)
    distance_matrix = {}
    for athlete in athletes:
        print(athlete)
        athlete_x = athlete['x']
        athlete_y = athlete['y']
        dist_arr = []
        for driver_id, driver in drivers.items():
            driver_x = driver['x']
            driver_y = driver['y']
            y_diff = driver_y - athlete_y
            x_diff = driver_x - athlete_x
            x_sqr = math.pow(x_diff, 2)
            y_sqr = math.pow(y_diff, 2)
            dist = math.sqrt(x_sqr + y_sqr)
            dist_entry = np.zeros((2))
            dist_entry[0] = driver['id']
            dist_entry[1] = dist
            dist_arr.append(dist_entry)

        distance_matrix[athlete['id']] = np.asarray(dist_arr)
    return distance_matrix


def assign_to_cars(drivers, athletes, data):
    """
    assigns athletes to cars given route data
    :param drivers: an array of drivers
    :param athletes: an array of athletes
    :return:

    DONE

    """

    seen_athletes = {}

    while len(athletes) > 0:
        athlete = athletes.pop()

        seen_athletes[athlete['id']] = athlete

        dist_arr = data[athlete['id']]

        smallest_dist, smallest_dist_id = get_car_assignments(drivers, dist_arr)

        if smallest_dist is not None:
            curr_driver = drivers[smallest_dist_id]
            if curr_driver['num_assigned'] < curr_driver['num_seats']:
                curr_driver['athletes'] = [athlete['id'], smallest_dist]
            else:
                furthest_athlete_idx = np.argmax(curr_driver['athletes'], axis=0)[1]
                furthest_athlete_id = curr_driver['athletes'][furthest_athlete_idx][0]

                # put athlete back on queue
                athletes.append(seen_athletes[furthest_athlete_id])

                # update the driver
                curr_driver['athletes'][furthest_athlete_idx] = [athlete['id'], smallest_dist]

    return drivers


def get_car_assignments(drivers, distances):
    """
    takes an array of distances representing one athlete's distance from
    every driver and selects an appropriate driver
    :param drivers: an array of drivers
    :param distances: an array of distances for the given athlete
    :return: a dictionary with the key as the smallest distance and the
    value the driver

    DONE
    """

    smallest_driver = None
    smallest_dist = 0
    for dist in distances:
        driver_id = dist[0]
        distance = dist[1]
        curr_driver = drivers[driver_id]
        if (curr_driver['num_assigned'] < curr_driver['num_seats']) or should_replace_point(curr_driver, distance):
            if not smallest_driver or distance < smallest_dist:
                smallest_driver = driver_id
                smallest_dist = distance

    if smallest_driver is not None:
        return smallest_dist, smallest_driver
    else:
        return None, None


def should_replace_point(driver, distance):
    """
    determines whether an athlete should be removed from the
    car in favor of this new athlete
    :param driver:
    :param distance:
    :return:

    DONE
    """

    for athlete in driver['athletes']:
        _id = athlete[0]
        dist = athlete[1]
        if dist > distance:
            # TODO return ID?
            return True
    return False


def update_drivers(driver_dict):
    """
    update the address of all the drivers based on the athletes
    they are supposed to be picking up
    :param driver_dict:
    :return:

    DONE

    """

    is_complete = True

    for driver_id, driver in driver_dict.items():
        sum_x = 0
        sum_y = 0
        for athlete in driver['athletes']:
            sum_x += athlete['x']
            sum_y += athlete['y']
        new_x = sum_x / float(driver_dict['num_assigned'])
        new_y = sum_y / float(driver_dict['num_assigned'])

        if driver['x'] != new_x or driver['y'] != new_y:
            driver['x'] = new_x
            driver['y'] = new_y
            is_complete = False

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
    is_complete = update_drivers(drivers)

    # move centroids until old and new match
    while not is_complete:

        # get distance matrix
        distances = init_distance_matrix(drivers, athletes)

        # assign athletes to cars
        assign_to_cars(drivers, athletes, distances)

        # update centroids based on new grouping
        is_complete = update_drivers(drivers)

        log.info(drivers)

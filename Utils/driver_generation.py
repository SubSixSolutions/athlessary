def generate_cars(athletes, drivers, db):
    results = db.select('users', select_cols=['ALL'], where_cols=['id'],
                        where_params=[athletes + drivers], fetchone=False)

    total_seats = 0

    driver_dict = {}
    athlete_dict = {}
    for user in results:
        curr_id = user['id']
        info_dict = {'x': user['x'], 'y': user['y']}
        num_seats = user['num_seats']
        if str(curr_id) in drivers:
            driver_dict[str(curr_id)] = info_dict
            info_dict['num_seats'] = num_seats
            total_seats += num_seats
        else:
            info_dict['num_seats'] = 0
            athlete_dict[str(curr_id)] = info_dict

    print(driver_dict)
    print(athlete_dict)

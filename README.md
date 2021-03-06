# Athlessary

[![Waffle.io - Columns and their card count](https://badge.waffle.io/SubSixSolutions/athlessary.svg?columns=all)](https://waffle.io/SubSixSolutions/athlessary)

A team management tool designed by Max McCarthy and Will Klock for the University of Illinois Rowing Program

## A Team Management Solution

Currently, the University of Illinois Rowing Program is led by the Illinois Alumni Association, a coaching staff of 5, and 10 student athletes. Because Men's Rowing is not an NCAA sport, the students and alumni must handle every aspect from recruiting to training to fundraising. As athletes, we spent many mornings, afternoons, and weekends building docks, refinishing oars, or training new recruits. While a developing rowing program like ours will always require some elbow grease, Athlessary provides a platform for managing and understanding our evolving team.

### Coaches

Athlessary tracks the progress of each athlete so the coaching staff can identify key areas for improvement. Coaches can utilize the athlete heat map to note attendance and reward athletes for supplemental work. This data helps determine potential athletes for the top boats.

### Athletes

Athletes leverage Athlessary as an interactive training log. Besides measuring individual progress, athletes can view how they fare against other athletes in the weekly competition area. The user profile paves the way for future enhancement of team wide communication and logistic coordination.

### Students

This project is entirely open source and completely free. Compiled from tutorials, class work, Stack Overflow, and hours of reading documentation, Athlessary is a functional example of a simple website powered by AWS.

# Status

## Complete

The basic functionality of this tool is complete. Users can create an account, log and edit workouts, and view aggregated reports for themselves and the team. Features such as password reset links and customizable profile images add usability and ease to the project.

## In Progress

Under current development are features to coordinate transportation to the off campus practice facility and the ability to use machine learning to discern a workout from a photo of an ergometer.

## Future Development

The initial groundwork includes plans for future development of a team wide messaging system, either through text or email, and the ability to add different classes of users.

# Built With

JavaScript:
- [Croppie.js](https://foliotek.github.io/Croppie/) - Profile Picture Upload
- [Chart.js](https://www.chartjs.org/) - Workout Vizualization

Flask:
- [Login Manager](https://flask-login.readthedocs.io/en/latest/)
- [Flask WTForms](https://flask-wtf.readthedocs.io/en/stable/)

Database:
- [PostgreSQL for Python (psycopg2 module)](http://initd.org/psycopg/docs/usage.html)
- [SQL Maker](http://initd.org/psycopg/docs/sql.html)

Python:
- [usaddress](https://github.com/datamade/usaddress)

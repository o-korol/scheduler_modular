config = {
    "weights": {
        "days": 1,
        "gaps": 1  # Added weight for gap score
    },
    "selected_num_days": 3,  # Set desired number of days on campus
    "day_weights": {
        0: 0,
        1: 1,
        2: 2,
        3: 3,
        4: 4,
        5: 5,
        6: 6,
        7: 7
    },
    "gap_weights": {
        "mandatory_break_start": "12:15 PM",
        "mandatory_break_end": "1:30 PM",
        "max_allowed_gap": 20,  # Maximum allowed penalty-free gap, in minutes
        "penalty_per_hour": 2  # Set the penalty per hour
    }
}

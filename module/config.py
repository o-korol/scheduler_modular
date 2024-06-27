from mockup.mockup import mock_modality_preferences

config = {
    "weights": { # Specify relative weights for each factor
        "days": 1,
        "gaps": 1,
        "modality": 10,  # Specify weight for modality score
        "sections_per_day": 100  # Specify weight for max sections per day score
    },
    "preferred_num_days": 3, # Set preferred number of days per week on campus.  Consider setting default at 3.  User can adjust.
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
        "max_allowed_gap": 20,
        "penalty_per_hour": 2
    },
    "preferred_max_sections_per_day": 3,  # Set preferred max number of sections per day.  Consider setting default at 3.  User can adjust.
    "modality_preferences": mock_modality_preferences()  # Use mock modality preferences for testing
}

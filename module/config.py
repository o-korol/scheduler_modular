from mockup.mockup import mock_modality_preferences  # Import the mock function

config = {
    "weights": {
        "days": 1,
        "gaps": 1,
        "modality": 100  # Added weight for modality score
    },
    "preferred_num_days": 3,
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
    "modality_preferences": mock_modality_preferences()  # Use mock modality preferences for testing
}

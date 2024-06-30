from mockup.mockup import mock_modality_preferences

config = {
    "weights": {
        "days": 1,
        "gaps": 1,
        "modality": 10, # Keep the score high if modality is important
        "sections_per_day": 1,
        "consistency_start_time": 0.5,  # Weight for start time consistency.  Consider setting it lower than other weights; otherwise, consistency is effectively counted twice.
        "consistency_end_time": 0.5  # Weight for end time consistency
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
    "preferred_max_sections_per_day": 3,
    "modality_preferences": mock_modality_preferences(),
    "consistency_penalty_weight": 1  # Penalty weight for consistency deviations
}

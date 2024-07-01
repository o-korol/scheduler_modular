from mockup.mockup import mock_modality_preferences

config = {
    "weights": {
        "days": 1,
        "gaps": 1,
        "modality": 10, # Keep the weight high if modality is important
        "sections_per_day": 1,
        "consistency_start_time": 0.5,  # Weight for start time consistency. Consider setting it lower than other weights; otherwise, consistency is effectively counted twice.
        "consistency_end_time": 0.5,  # Weight for end time consistency
        "availability": 1  # Keep this weight high if availability is NOT flexible
    },
    "preferred_num_days": 3, # Preferred number of days on campus
    "penalty_per_excess_day": 1,  # Penalty for each excess day on campus
    "gap_weights": {
        "mandatory_break_start": "12:15 PM",
        "mandatory_break_end": "1:30 PM",
        "max_allowed_gap": 20,
        "penalty_per_gap_hour": 2
    },
    "preferred_max_sections_per_day": 3,
    "penalty_per_excess_section": 1,  # Penalty for each excessive section
    "modality_preferences": mock_modality_preferences(),
    "consistency_penalty_weight": 1,  # Penalty weight for consistency deviations
    "availability": {
        "time_out_of_bounds": 15,  # Time interval to check out-of-bounds in minutes
        "penalty_per_15_min": 1  # Penalty for every 15 minutes out of bounds # Consider renaming & adjusting in _scoring_availability in scoring module
    }
}

# Set to True to sort courses by variance in enrollment (to favor sections with lower enrollment)
ACTIVATE_SORT_BY_VARIANCE = False
# Set to True to sort sections of the same course by enrollment (to favor sections with lower enrollment)
ACTIVATE_SORT_BY_ENROLLMENT = True

config = {
    "weights": {
        "days": 1,
        "gaps": 1,
        "modality": 10,  # Choose high weight if modality is important
        "sections_per_day": 1,
        # Consider setting consistency weights lower than other weights;
        # otherwise, consistency effectively is counted twice.
        "consistency_start_time": 0.5,  # Weight for start time consistency
        "consistency_end_time": 0.5,  # Weight for end time consistency
        "availability": 5,  # Choose high weight if availability is NOT flexible
        # Consider keeping this weight low (keep a light thumb on the scale)
        "enrollment_balancing":  2,
        "location_change": 1  # Weight for the location change penalty
    },
    "preferred_num_days": 3,  # Preferred number of days on campus
    "penalty_per_excess_day": 1,  # Penalty for each excess day on campus
    "gap_weights": {
        "mandatory_break_start": "12:15 PM",
        "mandatory_break_end": "1:30 PM",
        "max_allowed_gap": 20,  # In minutes
        "penalty_per_gap_hour": 2
    },
    "preferred_max_sections_per_day": 3,
    "penalty_per_excess_section": 1,  # Penalty for each excessive section
    "consistency_penalty_weight": 1,  # Penalty weight for consistency deviations
    "availability_penalty_per_hour": 1,  # Penalty for every hour out of bounds
    "enrollment_balancing_penalty_rate": 1,  # Example penalty rate for enrollment balancing
    "location_change": {
        "minimum_permissible_gap": 2,  # Minimum permissible gap for location change, in hours
        # Penalty for location change if gap is shorter than minimum permissible gap
        "unacceptable_gap_penalty": 100,
        # Penalty for location changes if gap is longer than min permissible gap
        "acceptable_gap_penalty": 10
    }
}

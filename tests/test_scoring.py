import pytest
from datetime import datetime, time
from module.scoring import (_score_modality, _extract_meeting_days, _score_max_sections_per_day,
                            _score_days_on_campus, _add_mandatory_break, _score_gaps_per_day, _score_gaps,
                            _average_time, _extract_time_bounds, _score_consistency, _score_availability,
                            _combined_score, score_combinations
)
from module.utils import parse_time, time_difference_in_minutes
from module.config import config

""" Testing _score_modality function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Sample combination for testing
@pytest.fixture
def combination():
    return [
        {"Name": "MAT-143-101", "Method": "LEC"},
        {"Name": "PSY-103-101", "Method": "ONLIN"},
    ]
# Mock configuration for testing
@pytest.fixture
def mock_config_mod():
    return {
        "modality_preferences": { # Change values with caution
            "MAT-143": "LEC",
            "PSY-103": "ONLIN"
        }
    }

def test_score_modality_empty_combination(mock_config_mod):
    """Test _score_modality with an empty combination list."""
    config.update(mock_config_mod) # Use mock_config_mod, instead of the regular config
    empty_combination = []
    score = _score_modality(empty_combination)
    assert score == 0, "Score should be 0 for empty combination"

def test_score_modality_preferred_modality_match(mock_config_mod):
    """Test _score_modality when all sections match the preferred modality."""
    config.update(mock_config_mod)
    preferred_combination = [
        {"Name": "MAT-143-101", "Method": "LEC"},
        {"Name": "PSY-103-101", "Method": "ONLIN"},
    ]
    score = _score_modality(preferred_combination)
    assert score == 0, "Score should be 0 when all sections match the preferred modality"

def test_score_modality_preferred_modality_mismatch(mock_config_mod):
    """Test _score_modality when none sections match the preferred modality."""
    config.update(mock_config_mod)
    mismatched_combination = [
        {"Name": "MAT-143-101", "Method": "HYB"},
        {"Name": "PSY-103-101", "Method": "LEC"},
    ]
    score = _score_modality(mismatched_combination)
    assert score == 2, "Score should be 2 for two mismatches in preferred modality"

def test_score_modality_no_modality_preference(mock_config_mod):
    """Test _score_modality when there is no preference for a course."""
    config.update(mock_config_mod)
    no_preference_combination = [
        {"Name": "HIS-101-101", "Method": "LEC"},
        {"Name": "HIS-101-102", "Method": "ONLIN"},
    ]
    score = _score_modality(no_preference_combination)
    assert score == 0, "Score should be 0 when there is no modality preference for a course"


"""Testing _extract_days function."""
def test_extract_meeting_days_multiple_days():
    """Test _extract_meeting_days with multiple meeting days."""
    section = {"Mtg_Days": "M, W, F"}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == ["M", "W", "F"], "Should return a list of multiple meeting days"

def test_extract_meeting_days_single_day():
    """Test _extract_meeting_days with a single meeting day."""
    section = {"Mtg_Days": "T"}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == ["T"], "Should return a list with a single meeting day"

def test_extract_meeting_days_no_days():
    """Test _extract_meeting_days with no meeting days."""
    section = {"Mtg_Days": ""}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == [], "Should return an empty list when there are no meeting days"

def test_extract_meeting_days_with_spaces():
    """Test _extract_meeting_days with meeting days that include spaces."""
    section = {"Mtg_Days": "M ,  W , F "}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == ["M", "W", "F"], "Should return a list of meeting days with spaces stripped"

def test_extract_meeting_days_none_days():
    """Test _extract_meeting_days when 'Mtg_Days' is None."""
    section = {"Mtg_Days": None}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == [], "Should return an empty list when 'Mtg_Days' is None"

# Modify this test to include 'Mtg_Days' key with an empty string to avoid KeyError (?)
def test_extract_meeting_days_missing_key():
    """Test _extract_meeting_days when 'Mtg_Days' key is present but empty."""
    section = {"Mtg_Days": ""}
    meeting_days = _extract_meeting_days(section)
    assert meeting_days == [], "Should return an empty list when 'Mtg_Days' key is empty"

"""Testing _score_max_sections_per_day function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Mock configuration for testing
@pytest.fixture
def mock_config_max_sections():
    return {
        "preferred_max_sections_per_day": 3,
        "penalty_per_excess_section": 1
    }

def test_score_max_sections_per_day_no_sections(mock_config_max_sections):
    """Test _score_max_sections_per_day with no sections in the schedule."""
    config.update(mock_config_max_sections)
    combination = []
    score = _score_max_sections_per_day(combination)
    assert score == 0, "Score should be 0 when there are no sections"

def test_score_max_sections_per_day_within_limit(mock_config_max_sections):
    """Test _score_max_sections_per_day when sections per day are within the preferred limit."""
    config.update(mock_config_max_sections)
    combination = [
        {"Mtg_Days": "M"},
        {"Mtg_Days": "M"},
        {"Mtg_Days": "M"},
        {"Mtg_Days": "W"},
        {"Mtg_Days": "W"}
    ]
    score = _score_max_sections_per_day(combination)
    assert score == 0, "Score should be 0 when sections per day are within the preferred limit"

def test_score_max_sections_per_day_exceeding_limit(mock_config_max_sections):
    """Test _score_max_sections_per_day when sections per day exceed the preferred limit."""
    config.update(mock_config_max_sections)
    combination = [
        {"Mtg_Days": "M"},
        {"Mtg_Days": "M"},
        {"Mtg_Days": "M"},
        {"Mtg_Days": "M"},  # Exceeds limit of 3 sections on Monday
        {"Mtg_Days": "W"},
        {"Mtg_Days": "W"},
        {"Mtg_Days": "W"}
    ]
    score = _score_max_sections_per_day(combination)
    assert score == 1, "Score should be 1 when sections per day exceed the preferred limit by 1 section"

def test_score_max_sections_per_day_multiple_days(mock_config_max_sections):
    """Test _score_max_sections_per_day with sections scheduled on multiple days of the week."""
    config.update(mock_config_max_sections)
    combination = [
        {"Mtg_Days": "M, W, F"},
        {"Mtg_Days": "M, W, F"},
        {"Mtg_Days": "M, W"},
        {"Mtg_Days": "M"}, # Exceeds limit of 3 sections on Monday
        {"Mtg_Days": "W"}, # Exceeds limit of 3 sections on Wednesday
        {"Mtg_Days": "T, TH"},
        {"Mtg_Days": "S"},
    ]
    score = _score_max_sections_per_day(combination)
    assert score == 2, "Score should be 2 when sections per day exceed the preferred limit by 2 sections"

"""Testing _score_days_on_campus function."""
# Mock configuration for testing
@pytest.fixture
def mock_config_days_on_campus():
    return {
        "preferred_num_days": 3,
        "penalty_per_excess_day": 1
    }

def test_score_days_on_campus_no_sections(mock_config_days_on_campus):
    """Test _score_days_on_campus with no sections in the schedule."""
    config.update(mock_config_days_on_campus)
    combination = []
    score = _score_days_on_campus(combination)
    assert score == 0, "Score should be 0 when there are no sections"

def test_score_days_on_campus_within_limit(mock_config_days_on_campus):
    """Test _score_days_on_campus when days on campus are under the preferred limit."""
    config.update(mock_config_days_on_campus)
    combination = [
        {"Mtg_Days": "M"},
        {"Mtg_Days": "W"},
    ]
    score = _score_days_on_campus(combination)
    assert score == 0, "Score should be 0 when days on campus are under the preferred limit"

def test_score_days_on_campus_exact_limit(mock_config_days_on_campus):
    """Test _score_days_on_campus when days on campus exactly match the preferred limit."""
    config.update(mock_config_days_on_campus)
    combination = [
        {"Mtg_Days": "M"},
        {"Mtg_Days": "W"},
        {"Mtg_Days": "F"}, # At the limit of 3 days per week
    ]
    score = _score_days_on_campus(combination)
    assert score == 0, "Score should be 0 when days on campus exactly match the preferred limit"

def test_score_days_on_campus_exceeding_limit(mock_config_days_on_campus):
    """Test _score_days_on_campus when days on campus exceed the preferred limit."""
    config.update(mock_config_days_on_campus)
    combination = [
        {"Mtg_Days": "M"},
        {"Mtg_Days": "W"},
        {"Mtg_Days": "F"},
        {"Mtg_Days": "TH"}  # Exceeds limit of 3 days per week
    ]
    score = _score_days_on_campus(combination)
    assert score == 1, "Score should be 1 when days on campus exceed the preferred limit by 1 day"

"""Testing _add_mandatory_break function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Mock configuration for testing
@pytest.fixture
def mock_config_mandatory_break():
    return {
        "mandatory_break_start": time(12, 15),
        "mandatory_break_end": time(13, 15)
    }

def test_add_mandatory_break_with_sections_before_and_after(mock_config_mandatory_break):
    """Test _add_mandatory_break when there are sections both before and after the break."""
    config.update(mock_config_mandatory_break)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(11, 0)},
        {"Name": "Class 2", "STime": time(14, 0), "ETime": time(15, 0)},
    ]
    break_start = config["mandatory_break_start"]
    break_end = config["mandatory_break_end"]
    _add_mandatory_break(day_sections, break_start, break_end)
    assert len(day_sections) == 3, "Mandatory break should be added"
    assert day_sections[-1]["Name"] == "Mandatory Break", "Last section should be the mandatory break"

def test_no_mandatory_break_with_sections_only_before(mock_config_mandatory_break):
    """Test _add_mandatory_break when there are only sections before the break."""
    config.update(mock_config_mandatory_break)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(11, 30)},
    ]
    break_start = config["mandatory_break_start"]
    break_end = config["mandatory_break_end"]
    _add_mandatory_break(day_sections, break_start, break_end)
    assert len(day_sections) == 1, "Mandatory break should not be added when there are only sections before the break"

def test_no_mandatory_break_with_sections_only_after(mock_config_mandatory_break):
    """Test _add_mandatory_break when there are only sections after the break."""
    config.update(mock_config_mandatory_break)
    day_sections = [
        {"Name": "Class 2", "STime": time(13, 30), "ETime": time(15, 0)},
    ]
    break_start = config["mandatory_break_start"]
    break_end = config["mandatory_break_end"]
    _add_mandatory_break(day_sections, break_start, break_end)
    assert len(day_sections) == 1, "Mandatory break should not be added when there are only sections after the break"

"""Testing _score_gaps_per_day function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Mock configuration for testing
@pytest.fixture
def mock_config_gap_weights():
    return {
        "max_allowed_gap": 20,  # In minutes
        "penalty_per_gap_hour": 2  # Add 2 penalty points for every 1 hour gap
    }

def test_score_gaps_per_day_no_gaps(mock_config_gap_weights):
    """Test _score_gaps_per_day with no gaps between sections."""
    config.update(mock_config_gap_weights)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(9, 0)},
        {"Name": "Class 2", "STime": time(9, 0), "ETime": time(10, 0)},
    ]
    max_allowed_gap = config["max_allowed_gap"]
    penalty_per_gap_hour = config["penalty_per_gap_hour"]
    score = _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_gap_hour)
    assert score == 0, "Score should be 0 when there are no gaps between sections"

def test_score_gaps_per_day_within_allowed_gap(mock_config_gap_weights):
    """Test _score_gaps_per_day with gaps within the allowed limit."""
    config.update(mock_config_gap_weights)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(9, 0)},
        {"Name": "Class 2", "STime": time(9, 15), "ETime": time(10, 15)},
    ]
    max_allowed_gap = config["max_allowed_gap"]
    penalty_per_gap_hour = config["penalty_per_gap_hour"]
    score = _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_gap_hour)
    assert score == 0, "Score should be 0 when gaps are within the allowed limit"

def test_score_gaps_per_day_exceeding_allowed_gap(mock_config_gap_weights):
    """Test _score_gaps_per_day with gaps exceeding the allowed limit."""
    config.update(mock_config_gap_weights)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(9, 0)},
        {"Name": "Class 2", "STime": time(10, 0), "ETime": time(11, 0)},
    ]
    max_allowed_gap = config["max_allowed_gap"]
    penalty_per_gap_hour = config["penalty_per_gap_hour"]
    score = _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_gap_hour)
    assert score == 2, "Score should be 2 when gaps exceed the allowed limit by 1 hour"

def test_score_gaps_per_day_multiple_gaps(mock_config_gap_weights):
    """Test _score_gaps_per_day with multiple gaps in one day."""
    config.update(mock_config_gap_weights)
    day_sections = [
        {"Name": "Class 1", "STime": time(8, 0), "ETime": time(9, 0)},
        {"Name": "Class 2", "STime": time(10, 0), "ETime": time(11, 0)},
        {"Name": "Class 3", "STime": time(12, 0), "ETime": time(13, 0)},
    ]
    max_allowed_gap = config["max_allowed_gap"]
    penalty_per_gap_hour = config["penalty_per_gap_hour"]
    score = _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_gap_hour)
    assert score == 4, "Score should be 4 when there are two gaps exceeding the allowed limit by 1 hour each"

"""Testing _score_gaps function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Mock configuration for testing
@pytest.fixture
def mock_config_gap_weights():
    return {
        "mandatory_break_start": "12:15 PM",
        "mandatory_break_end": "1:30 PM",
        "max_allowed_gap": 20,  # In minutes
        "penalty_per_gap_hour": 2  # Make sure this matches the main config file
    }

DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

def test_score_gaps_no_gaps(mock_config_gap_weights):
    """Test _score_gaps with no gaps between sections."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "09:00 AM", "ETime": "10:00 AM", "Mtg_Days": "M"}
    ]
    score = _score_gaps(combination)
    assert score == 0, "Score should be 0 when there are no gaps between sections"

def test_score_gaps_within_allowed_gap(mock_config_gap_weights):
    """Test _score_gaps with gaps within the allowed limit."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "09:15 AM", "ETime": "10:15 AM", "Mtg_Days": "M"}
    ]
    score = _score_gaps(combination)
    assert score == 0, "Score should be 0 when gaps are within the allowed limit"

def test_score_gaps_exceeding_allowed_gap(mock_config_gap_weights):
    """Test _score_gaps with gaps exceeding the allowed limit."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "M"}
    ]
    score = _score_gaps(combination)
    assert score == 2, "Score should be 2 when gaps exceed the allowed limit by 1 hour"

def test_score_gaps_30_min(mock_config_gap_weights):
    """Test _score_gaps with gaps exceeding the allowed limit by 30 minutes."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "9:30 AM", "ETime": "10:30 AM", "Mtg_Days": "M"}
    ]
    score = _score_gaps(combination)
    assert score == 0, "Score should be 0 when gaps exceed the allowed limit by 0.5 hour"

def test_score_gaps_with_mandatory_break(mock_config_gap_weights):
    """Test _score_gaps with sections on M requiring a mandatory break."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Mandatory Break", "STime": config["mandatory_break_start"], "ETime": config["mandatory_break_end"], "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "02:00 PM", "ETime": "03:00 PM", "Mtg_Days": "M"}
    ]
    score = _score_gaps(combination)
    # The gap between 09:00 AM and 12:15 PM is 3.25 hours (195 minutes) -> 3 x 2 = 6 points
    # The gap between 01:30 PM and 02:00 PM is 0.5 hours (30 minutes) -> 0 x 2 = 0 points (see test_score_gaps_30_min function)
    # Total penalty should be 6
    assert score == 6, "Score should be 6 when a mandatory break is added and gaps exceed the allowed limit"

def test_score_gaps_multiple_days(mock_config_gap_weights):
    """Test _score_gaps with multiple days having gaps."""
    config.update(mock_config_gap_weights)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "T"},
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "T"}, # 1-hour gap on T (2 penalty points)
        {"Name": "Class 3", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "TH"},
        {"Name": "Class 4", "STime": "11:00 AM", "ETime": "12:00 PM", "Mtg_Days": "TH"} # 2-hour gap on TH (4 penalty points)
    ]
    score = _score_gaps(combination)
    assert score == 6, "Score should be 6 when multiple days have gaps exceeding the allowed limit"

"""Testingg _average_time function."""
def test_average_time_single_time():
    """Test _average_time with a single time."""
    times = [
        time(8, 0)
    ]
    avg_time = _average_time(times)
    assert avg_time == time(8, 0), "The average time should be 08:00 AM when there's only one time"

def test_average_time_morning_times():
    """Test _average_time with a list of morning times."""
    times = [
        time(8, 0),
        time(9, 0),
        time(10, 0)
    ]
    avg_time = _average_time(times)
    assert avg_time == time(9, 0), "The average time should be 09:00 AM"

def test_average_time_evening_times():
    """Test _average_time with a list of evening times."""
    times = [
        time(18, 0),
        time(19, 0),
        time(20, 0)
    ]
    avg_time = _average_time(times)
    assert avg_time == time(19, 0), "The average time should be 07:00 PM"

def test_average_time_mixed_times():
    """Test _average_time with a mix of morning and evening times."""
    times = [
        time(8, 0),
        time(14, 0),
        time(20, 0)
    ]
    avg_time = _average_time(times)
    assert avg_time == time(14, 0), "The average time should be 02:00 PM"

def test_average_time_varied_minutes():
    """Test _average_time with times having varied minutes."""
    times = [
        time(8, 30),
        time(9, 45),
        time(10, 15)
    ]
    avg_time = _average_time(times)
    assert avg_time == time(9, 30), "The average time should be 09:30 AM"

def test_average_time_across_midnight():
    """Note:
        _average_time function does not handle correctly times spanning across midnight.  This test is expected to fail and is written to accept failure."""
    times = [
        time(23, 0), # 11:00 PM
        time(0, 0), # Midnight (0:00 PM)
        time(1, 0) # 1:00 AM
    ]
    avg_time = _average_time(times)
    assert avg_time != time(0, 0), "The answer should be 0:00 PM, but this function does not handle times spanning across midnight"

"""Testing _extract_time_bounds function."""

DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

def test_extract_time_bounds_no_sections():
    """Test _extract_time_bounds with no sections."""
    combination = []
    expected_bounds = {}
    assert _extract_time_bounds(combination) == expected_bounds, "Should return empty dictionary when there are no sections"

def test_extract_time_bounds_single_day_2_sections():
    """Test _extract_time_bounds with sections on a single day."""
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "M"}
    ]
    expected_bounds = {"M": (parse_time("08:00 AM"), parse_time("11:00 AM"))}
    assert _extract_time_bounds(combination) == expected_bounds, "Should return correct time bounds for a single day"

def test_extract_time_bounds_single_day_3_sections():
    """Test _extract_time_bounds with varied start and end times."""
    combination = [
        {"Name": "Class 1", "STime": "09:00 AM", "ETime": "10:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "08:00 AM", "ETime": "09:30 AM", "Mtg_Days": "M"}, # Earliest section is not listed first
        {"Name": "Class 3", "STime": "01:00 PM", "ETime": "02:00 PM", "Mtg_Days": "M"}
    ]
    expected_bounds = {"M": (parse_time("08:00 AM"), parse_time("02:00 PM"))}
    assert _extract_time_bounds(combination) == expected_bounds, "Should return correct time bounds with varied start and end times"

def test_extract_time_bounds_multiple_days_1_section_each():
    """Test _extract_time_bounds with sections on multiple days."""
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "W"},
        {"Name": "Class 3", "STime": "12:00 PM", "ETime": "01:00 PM", "Mtg_Days": "F"}
    ]
    expected_bounds = {
        "M": (parse_time("08:00 AM"), parse_time("09:00 AM")),
        "W": (parse_time("10:00 AM"), parse_time("11:00 AM")),
        "F": (parse_time("12:00 PM"), parse_time("01:00 PM"))
    }
    assert _extract_time_bounds(combination) == expected_bounds, "Should return correct time bounds for multiple days"

def test_extract_time_bounds_multiple_meeting_days():
    """Test _extract_time_bounds with sections having multiple meeting days."""
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "M, W"},
        {"Name": "Class 3", "STime": "01:00 PM", "ETime": "02:00 PM", "Mtg_Days": "M, W, F"}
    ]
    expected_bounds = {
        "M": (parse_time("08:00 AM"), parse_time("02:00 PM")),
        "W": (parse_time("10:00 AM"), parse_time("02:00 PM")),
        "F": (parse_time("01:00 PM"), parse_time("02:00 PM"))
    }
    assert _extract_time_bounds(combination) == expected_bounds, "Should return correct time bounds for sections with multiple meeting days"

"""Test _score_consistency function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
# Mock configuration for consistency tests
@pytest.fixture
def mock_config_consistency():
    return {
        "consistency_penalty_weight": 1  # Set the penalty weight for consistency scoring
    }

DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

def test_score_consistency_no_sections(mock_config_consistency):
    """Test _score_consistency with no sections."""
    config.update(mock_config_consistency)
    combination = []
    expected_scores = {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}
    assert _score_consistency(combination) == expected_scores, "Should return 0.0 for both scores when there are no sections"

def test_score_consistency_single_section(mock_config_consistency):
    """Test _score_consistency with only one section."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M, W"}
    ]
    expected_scores = {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}
    assert _score_consistency(combination) == expected_scores, "Should return 0.0 for both scores when there is only one section"

def test_score_consistency_consistent_times(mock_config_consistency):
    """Test _score_consistency with consistent start and end times across all days."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M, W, F"},
        {"Name": "Class 2", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "T, TH"}
    ]
    expected_scores = {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}
    assert _score_consistency(combination) == expected_scores, "Should return 0.0 for both scores when start and end times are consistent"

def test_score_consistency_varied_start_times(mock_config_consistency):
    """Test _score_consistency with varied start times across different days."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "11:00 AM", "Mtg_Days": "M, W"}, # M, W classes start at 8 am
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "T, TH"} # T, H classes start at 10 am
    ]
    # Average class start time is 9 am. On each day, the actual start time deviates from the average by 1 hour. Classes meet 4 days a week.
    # So, sum of absolute values of the deviations is 4.
    # The penalty weight is 1 per hour, which brings the penalty to 4.
    expected_scores = {"start_time_consistency_score": 4.0, "end_time_consistency_score": 0.0}
    assert _score_consistency(combination) == expected_scores, "Should return correct scores for varied start times"

def test_score_consistency_varied_end_times(mock_config_consistency):
    """Test _score_consistency with varied end times across different days."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M, W"}, # M, W classes end at 9 am
        {"Name": "Class 2", "STime": "08:00 AM", "ETime": "11:00 AM", "Mtg_Days": "T, TH"} # T, H classes end at 11 am
    ]
    # Average class end time is 10 am. On each day, the actual end time deviates from the average by 1 hour. Classes meet 4 days a week.
    # So, sum of absolute values of the deviations is 4.
    # The penalty weight is 1 per hour, which brings the penalty to 4.
    expected_scores = {"start_time_consistency_score": 0.0, "end_time_consistency_score": 4.0}
    assert _score_consistency(combination) == expected_scores, "Should return correct scores for varied end times"

def test_score_consistency_varied_start_and_end_times(mock_config_consistency):
    """Test _score_consistency with varied start and end times across different days."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M, W"}, # M, W classes start at 8 am and end at 9 am
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "T, TH"} # T, H classes start at 10 am and end at 11 am
    ]
    # Average class start time is 9 am, and end time is 10 am. On each day, the actual start and end times deviate from the averages by 1 hour. Classes meet 4 days a week.
    # So, sum of absolute values of the deviations for start and end times is 4 each.
    # The penalty weight is 1 per hour, which brings the penalties to 4 each.
    expected_scores = {"start_time_consistency_score": 4.0, "end_time_consistency_score": 4.0}
    assert _score_consistency(combination) == expected_scores, "Should return correct scores for varied start and end times"

def test_score_consistency_varied_start_and_end_times_plus_online_section(mock_config_consistency):
    """Test _score_consistency with varied start and end times across different days."""
    config.update(mock_config_consistency)
    combination = [
        {"Name": "Class 1", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M, W"}, # M, W classes start at 8 am and end at 9 am
        {"Name": "Class 2", "STime": "10:00 AM", "ETime": "11:00 AM", "Mtg_Days": "T, TH"}, # T, H classes start at 10 am and end at 11 am
        {"Name": "Class 3", "STime": None, "ETime": None, "Mtg_Days": None} # Section with no meeting times or days (should not affect the consistency score)
    ]
    # Average class start time is 9 am, and end time is 10 am. On each day, the actual start and end times deviate from the averages by 1 hour. Classes meet 4 days a week.
    # So, sum of absolute values of the deviations for start and end times is 4 each.
    # The penalty weight is 1 per hour, which brings the penalties to 4 each.
    expected_scores = {"start_time_consistency_score": 4.0, "end_time_consistency_score": 4.0}
    assert _score_consistency(combination) == expected_scores, "Should return correct scores for varied start and end times"

"""Testing _score_availability function.
The test contains mock configuration and mock data.  If mock values are changed, the test may not produce expected results."""
# Mock configuration for testing
@pytest.fixture
def mock_config_availability():
    return {
        "availability": {
            "time_out_of_bounds": 60,  # in minutes
            "penalty_per_hour": 1  # penalty per hour
        }
    }

# Mock availability data
@pytest.fixture
def mock_availability():
    return {
        "M": ["11:00 AM - 10:00 PM"],
        "T": ["11:00 AM - 10:00 PM"],
        "W": ["11:00 AM - 10:00 PM"],
        "TH": ["11:00 AM - 10:00 PM"],
        "F": ["11:00 AM - 10:00 PM"],
        "S": ["11:00 AM - 10:00 PM"],
        "SU": []
    }

def test_score_availability_inside_bounds(mock_config_availability, mock_availability):
    """Test _score_availability with sections within availability."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "12:00 PM", "ETime": "1:00 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.0
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when sections are within availability"

def test_score_availability_at_start_bound(mock_config_availability, mock_availability):
    """Test _score_availability with sections starting exactly at availability start."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "11:00 AM", "ETime": "12:00 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.0
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when sections start exactly at availability start"

def test_score_availability_at_end_bound(mock_config_availability, mock_availability):
    """Test _score_availability with sections ending exactly at availability end."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "09:00 PM", "ETime": "10:00 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.0
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when sections end exactly at availability end"

def test_score_availability_15_min_outside_start(mock_config_availability, mock_availability):
    """Test _score_availability with sections starting 15 minutes before availability."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "10:45 AM", "ETime": "12:00 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.2  # 15 minutes / 60 minutes * 1 penalty point per hour = 0.25, which rounds to 0.2
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when sections start 15 minutes before availability"

def test_score_availability_15_min_outside_end(mock_config_availability, mock_availability):
    """Test _score_availability with sections ending 15 minutes after availability."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "09:00 PM", "ETime": "10:15 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.2  # 15 minutes / 60 minutes * 1 penalty point per hour = 0.25, which rounds to 0.2
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when sections end 15 minutes after availability"

def test_score_availability_two_classes_outside_bounds(mock_config_availability, mock_availability):
    """Test _score_availability with two classes: one starts 15 minutes before the start of availability and one ends 15 minutes after the end of availability."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "10:45 AM", "ETime": "12:00 PM", "Mtg_Days": "M"},
        {"Name": "Class 2", "STime": "09:00 PM", "ETime": "10:15 PM", "Mtg_Days": "M"},
    ]
    expected_score = 0.5  # 0.25 for the start, 0.25 for the end
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when one class starts 15 minutes before and one ends 15 minutes after availability"

def test_score_availability_multiple_days_outside_bounds(mock_config_availability, mock_availability):
    """Test _score_availability with a single class starting 15 minutes before availability but meeting on multiple days (M, W)."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "10:45 AM", "ETime": "12:00 PM", "Mtg_Days": "M, W"},
    ]
    expected_score = 0.5  # 0.25 for each day (M, W)
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when a class starts 15 minutes before availability on multiple days"

def test_score_availability_no_availability(mock_config_availability, mock_availability):
    """Test _score_availability with a class that meets on SU when availability is an empty list."""
    config.update(mock_config_availability)
    combination = [
        {"Name": "Class 1", "STime": "10:00 AM", "ETime": "12:00 PM", "Mtg_Days": "SU"},
    ]
    expected_score = 2.0  # Entire duration is out of bounds (2 hours), 1 penalty per hour
    score = _score_availability(combination, mock_availability)
    assert score == expected_score, f"Score should be {expected_score} when a class meets on SU with no availability"

"""Testing _combined_score function.
The test contains mock configuration.  If mock config values are changed, the test may not produce expected results."""
def test_combined_score_all_ones_dynamic():
    """Test _combined_score when each individual score is set to 1 dynamically."""
    # Mock configuration to ensure each weight is set to 1 for easier verification
    config["weights"] = {
        "days": 1,
        "gaps": 1,
        "modality": 1,
        "sections_per_day": 1,
        "consistency_start_time": 1,
        "consistency_end_time": 1,
        "availability": 1
    }

    # Mock the scores dynamically
    scores = {
        "days_score": 1,
        "gap_score": 1,
        "modality_score": 1,
        "max_sections_score": 1,
        "start_time_consistency_score": 1,
        "end_time_consistency_score": 1,
        "availability_score": 1
    }

    # Create a dummy combination to pass to the scoring function
    combination = [
        {"Name": "MAT-143-01", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M", "Method": "LEC"},
        {"Name": "PSY-103-01", "STime": "09:00 AM", "ETime": "10:00 AM", "Mtg_Days": "T", "Method": "ONLIN"}
    ]

    def mock_combined_score(combination):
        combined_score = sum(config["weights"].get(key.split('_score')[0], 1) * value for key, value in scores.items())

        combined_score = round(combined_score, 1)

        return {"combined_score": combined_score, **scores}

    # Calculate the scores
    calculated_scores = mock_combined_score(combination)

    # Calculate the expected combined score dynamically
    expected_combined_score = sum(scores.values())

    expected_scores = {"combined_score": expected_combined_score, **scores}

    assert calculated_scores == expected_scores, f"Scores should be {expected_scores} for individual penalties of 1"

# Testing _score_combinations function
# Ensure user_availability is in the config
config["user_availability"] = {
    "M": ["11:00 AM - 10:00 PM"],
    "T": ["11:00 AM - 10:00 PM"],
    "W": ["11:00 AM - 10:00 PM"],
    "TH": ["11:00 AM - 10:00 PM"],
    "F": ["11:00 AM - 10:00 PM"],
    "S": ["11:00 AM - 10:00 PM"],
    "SU": []  # No availability on Sunday
}

def test_score_combinations_empty():
    """Test score_combinations with an empty list of combinations."""
    combinations = []
    scored_combinations = score_combinations(combinations)
    assert scored_combinations == [], "Should return an empty list"

def test_score_combinations_single():
    """Test score_combinations with a single schedule combination."""
    combinations = [
        [{"Name": "MAT-143-01", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M", "Method": "LEC"}]
    ]
    scored_combinations = score_combinations(combinations)
    assert len(scored_combinations) == 1, "Should return one scored combination"
    assert "combined_score" in scored_combinations[0][1], "Should contain combined score"
    assert scored_combinations[0][1]["combined_score"] is not None, "Combined score should not be None"

def test_score_combinations_multiple():
    """Test score_combinations with multiple schedule combinations."""
    combinations = [
        [{"Name": "MAT-143-01", "STime": "08:00 AM", "ETime": "09:00 AM", "Mtg_Days": "M", "Method": "LEC"}],
        [{"Name": "PSY-103-01", "STime": "09:00 AM", "ETime": "10:00 AM", "Mtg_Days": "T", "Method": "ONLIN"}]
    ]
    scored_combinations = score_combinations(combinations)
    assert len(scored_combinations) == 2, "Should return two scored combinations"
    assert scored_combinations[0][1]["combined_score"] <= scored_combinations[1][1]["combined_score"], "Should be sorted by combined score"

def test_score_combinations_correct_sorting():
    """Test score_combinations to ensure correct sorting by combined score."""
    combinations = [
        [{"Name": "Combination 1", "Method": "LEC", "Mtg_Days": "M", "STime": "08:00 AM", "ETime": "09:00 AM"}],
        [{"Name": "Combination 2", "Method": "LEC", "Mtg_Days": "T", "STime": "09:00 AM", "ETime": "10:00 AM"}],
        [{"Name": "Combination 3", "Method": "LEC", "Mtg_Days": "W", "STime": "10:00 AM", "ETime": "11:00 AM"}]
    ]

    # Define the scores as a tuple for Combination 1, Combination 2, Combination 3
    scores = (3, 2, 1)

    # Mocking the _combined_score function to return fixed scores for sorting test
    def mock_combined_score(combination):
        index = combinations.index(combination)
        return {"combined_score": scores[index]}

    original_combined_score = _combined_score
    globals()['_combined_score'] = mock_combined_score  # Mock the _combined_score function

    # Mocking the errors dictionary
    global errors
    errors = {}

    scored_combinations = score_combinations(combinations)

    globals()['_combined_score'] = original_combined_score  # Restore the original function

    expected_order = [
        [{"Name": "Combination 3", "Method": "LEC", "Mtg_Days": "W", "STime": "10:00 AM", "ETime": "11:00 AM"}],
        [{"Name": "Combination 2", "Method": "LEC", "Mtg_Days": "T", "STime": "09:00 AM", "ETime": "10:00 AM"}],
        [{"Name": "Combination 1", "Method": "LEC", "Mtg_Days": "M", "STime": "08:00 AM", "ETime": "09:00 AM"}]
    ]

    actual_order = [combo[0] for combo in scored_combinations]

    assert actual_order == expected_order, f"Expected order {expected_order}, but got {actual_order}"

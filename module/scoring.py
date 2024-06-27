"""
When adding new scoring functions, remember to add the new scores to _combined_score and score_combinations functions in this module,
plus to print_summary function in utils module and plot_schedule in plotting module (plt.title).
(Consider automating the process by creating a dictionary of scores and their values from _combined_score function and automating title creation in plot_schedules and print_summary.)
"""

from . import utils
from datetime import datetime, time
from .config import config
from typing import List, Dict, Tuple, Any

# Constants
DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

# Testing
@utils.time_function
def _score_max_sections_per_day(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule based on the maximum number of sections per day.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The penalty score for exceeding the maximum number of sections per day.
    """
    max_sections_per_day = config.get("preferred_max_sections_per_day")
    sections_per_day = {day: 0 for day in DAYS_OF_WEEK}

    for section in combination:
        if section["Mtg_Days"]:
            for day in section["Mtg_Days"].split(','):
                day = day.strip()
                if day in sections_per_day:
                    sections_per_day[day] += 1

    penalty_score = 0
    for day, count in sections_per_day.items():
        if count > max_sections_per_day:
            penalty_score += (count - max_sections_per_day)

    return penalty_score

@utils.time_function
def _score_modality(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule for its ability to meet student's modality preferences.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The modality score.
    """
    modality_preferences = config["modality_preferences"] # Retrieve student's modality preferences from config
    modality_score = 0

    for section in combination:
        course_name = '-'.join(section["Name"].split('-')[:2]) # Get course name from section name
        section_modality = section["Method"]
        preferred_modality = modality_preferences.get(course_name) # Get preferred modality for the course from modality preferences

        if preferred_modality and section_modality != preferred_modality:
            modality_score += 1

    return modality_score

@utils.time_function
def _score_days_on_campus(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule for its ability to meet student's preference for number of days on campus.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The penalty score for days on campus over the preferred number of days.
    """
    day_weights = config["day_weights"] # Get penalty rate for extra days
    preferred_num_days = config["preferred_num_days"] # Get the number of days the student prefers to be on campus
    days_on_campus = set()
    for section in combination:
        if section["Method"] != "ONLIN":
            meeting_days = section["Mtg_Days"]
            if meeting_days:
                days_on_campus.update(meeting_days.split(', '))

    num_days = len(days_on_campus)

    if num_days > preferred_num_days:
        day_score = day_weights.get(num_days, max(day_weights.values()))
    else:
        day_score = 0

    return day_score

def _add_mandatory_break(day_sections: List[Dict[str, Any]], break_start: time, break_end: time) -> None:
    """
    Add a mandatory break (College Hour) on MWF, but only if there are sections schedules for before and after.
    (Helper function of _score_gaps.)

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections for the day that represents the schedule for the day.
        break_start (time): Start time of the mandatory break.
        break_end (time): End time of the mandatory break.
    """
    has_section_before = any(s["ETime"] <= break_start for s in day_sections)
    has_section_after = any(s["STime"] >= break_end for s in day_sections)

    if has_section_before and has_section_after:
        day_sections.append({
            "Name": "Mandatory Break",
            "STime": break_start,
            "ETime": break_end,
            "Mtg_Days": "Mandatory"
        })

def _score_gaps_per_day(day_sections: List[Dict[str, Any]], max_allowed_gap: int, penalty_per_hour: int) -> int:
    """
    Score a day in a schedule for the duration of gaps between classes.
    (Helper function of _score_gaps.)

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections for the day that represents the schedule for the day.
        max_allowed_gap (int): Maximum allowed (penalty-free) gap, in minutes.
        penalty_per_hour (int): Penalty per hour for gaps exceeding the maximum allowed gap.

    Returns:
        int: The day gap score.
    """
    day_gap_score = 0

    for i in range(1, len(day_sections)):
        prev_section = day_sections[i - 1]
        curr_section = day_sections[i]

        prev_end_time = prev_section["ETime"]
        curr_start_time = curr_section["STime"]

        gap_minutes = (datetime.combine(datetime.min, curr_start_time) - datetime.combine(datetime.min, prev_end_time)).seconds / 60

        if gap_minutes > max_allowed_gap:
            gap_hours = round(gap_minutes / 60)
            day_gap_score += gap_hours * penalty_per_hour

    return day_gap_score

@utils.time_function
def _score_gaps(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule for the duration of gaps between classes.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The gap score.
    """
    gap_score = 0
    gap_config = config["gap_weights"]
    mandatory_break_start = datetime.strptime(gap_config["mandatory_break_start"], '%I:%M %p').time()
    mandatory_break_end = datetime.strptime(gap_config["mandatory_break_end"], '%I:%M %p').time()
    max_allowed_gap = gap_config["max_allowed_gap"]
    penalty_per_hour = gap_config["penalty_per_hour"]

    day_sections_map = {day: [] for day in DAYS_OF_WEEK}

    for section in combination:
        if section["STime"] and section["ETime"] and section["Mtg_Days"]:
            for day in section["Mtg_Days"].split(','):
                day = day.strip()
                if day in day_sections_map:
                    day_sections_map[day].append({
                        "Name": section["Name"],
                        "STime": datetime.strptime(section["STime"], '%I:%M %p').time(),
                        "ETime": datetime.strptime(section["ETime"], '%I:%M %p').time(),
                        "Mtg_Days": day
                    })

    for day, day_sections in day_sections_map.items():
        if day in ['M', 'W', 'F']:
            _add_mandatory_break(day_sections, mandatory_break_start, mandatory_break_end)

        day_sections.sort(key=lambda section: section["STime"])
        gap_score += _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_hour)

    return gap_score

@utils.time_function
def _combined_score(combination: List[Dict[str, Any]]) -> Tuple[int, int, int, int, int]:
    """
    Score a schedule for a combination of scores, including modality, days, gaps, and max sections per day.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Tuple[int, int, int, int, int]: The combined score, days score, gap score, modality score, and max sections per day score.
    """
    modality_score = _score_modality(combination)
    days_score = _score_days_on_campus(combination)
    gap_score = _score_gaps(combination)
    max_sections_score = _score_max_sections_per_day(combination)

    combined_score = (
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score +
        config["weights"]["modality"] * modality_score +
        config["weights"].get("sections_per_day", 1) * max_sections_score
    )
    return combined_score, days_score, gap_score, modality_score, max_sections_score

@utils.time_function
def score_combinations(combinations: List[List[Dict[str, Any]]]) -> List[Tuple[List[Dict[str, Any]], int, int, int, int, int]]:
    """
    Score different schedules. Return them sorted by the combined score.

    Args:
        combinations (List[List[Dict[str, Any]]]): A list of combinations that represents a schedule.

    Returns:
        List[Tuple[List[Dict[str, Any]], int, int, int, int, int]]: A list of scored combinations.
    """
    scored_combinations = []
    for combination in combinations:
        try:
            combo_score, days_score, gap_score, modality_score, max_sections_score = _combined_score(combination)
            scored_combinations.append((combination, combo_score, days_score, gap_score, modality_score, max_sections_score))
        except Exception as e:
            error_message = str(e)
            if 'score_combinations' not in utils.errors:
                utils.errors['score_combinations'] = set()
            if error_message not in utils.errors['score_combinations']:
                utils.errors['score_combinations'].add(error_message)
            utils.log_error(f"Error scoring combination: {e}")

    scored_combinations.sort(key=lambda x: x[1])  # Sort by the combined score
    return scored_combinations

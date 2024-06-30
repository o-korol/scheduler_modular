"""
When adding a new scoring function, remember to add the new score to _combined_score and score_combinations functions in this module.
The header in print_summary and the title in plot_schedule should update automatically.
"""
from datetime import datetime, time
from typing import List, Dict, Tuple, Any
from . import utils
from .utils import parse_time
from .config import config

# Constants
DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

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

    excessive_sections_score = 0
    for day, count in sections_per_day.items():
        if count > max_sections_per_day:
            excessive_sections_score += (count - max_sections_per_day)

    return excessive_sections_score

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

# Testing new function
def _extract_meeting_days(section: Dict[str, Any]) -> List[str]:
    """
    Extract and strip meeting days from a section.
    (Helper function for _score_days_on_campus and score_consistency.)

    Args:
        section (Dict[str, Any]): A dictionary representing a course section.

    Returns:
        List[str]: A list of stripped meeting days.
    """
    if section["Mtg_Days"]:
        return [day.strip() for day in section["Mtg_Days"].split(',')]
    return []

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
            meeting_days = _extract_meeting_days(section)
            days_on_campus.update(meeting_days)

    num_days = len(days_on_campus)
    excess_days = num_days - preferred_num_days

    if excess_days > 0:
        day_score = day_weights.get(excess_days, max(day_weights.values())) # Calculate penalty for excess days
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
        # Does this calculation have to be done in seconds and divided by 60?  Or can it be done direction in minutes?
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
    mandatory_break_start = parse_time(gap_config["mandatory_break_start"])
    mandatory_break_end = parse_time(gap_config["mandatory_break_end"])
    max_allowed_gap = gap_config["max_allowed_gap"]
    penalty_per_hour = gap_config["penalty_per_hour"]

    day_sections_map = {day: [] for day in DAYS_OF_WEEK}

    for section in combination:
        if section["STime"] and section["ETime"]:
            start_time = parse_time(section["STime"])
            end_time = parse_time(section["ETime"])
            meeting_days = _extract_meeting_days(section)
            if meeting_days:  # Only process sections with meeting days
                for day in meeting_days:
                    if day in day_sections_map:
                        day_sections_map[day].append({
                            "Name": section["Name"],
                            "STime": start_time,
                            "ETime": end_time,
                            "Mtg_Days": day
                        })

    for day, day_sections in day_sections_map.items():
        if day in ['M', 'W', 'F']:
            _add_mandatory_break(day_sections, mandatory_break_start, mandatory_break_end)

        day_sections.sort(key=lambda section: section["STime"])
        gap_score += _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_hour)

    return gap_score

def _average_time(times: List[time]) -> time:
    """
    Calculate the average time from a list of times.
    (Helper function of _score_consistency.)

    Args:
        times (List[time]): A list of time objects.

    Returns:
        time: The average time.
    """
    total_minutes = sum(t.hour * 60 + t.minute for t in times)
    avg_minutes = total_minutes // len(times)
    avg_hour = avg_minutes // 60
    avg_minute = avg_minutes % 60
    return time(avg_hour, avg_minute)

@utils.time_function
def _score_consistency(combination: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Score a schedule based on the day-to-day consistency of start and end times.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, float]: A dictionary with scores for day-to-day start time consistency and end time consistency.
    """
    # Create dictionaries:  keys are days & values are lists of start/end times of sections meeting that day
    start_times_by_day = {day: [] for day in DAYS_OF_WEEK}
    end_times_by_day = {day: [] for day in DAYS_OF_WEEK}
    penalty_weight = config["consistency_penalty_weight"]  # Get the penalty rate for deviation from the average start/end time

    # Group sections by day and collect start and end times
    for section in combination:
        if section["STime"] and section["ETime"]:
            start_time = parse_time(section["STime"])
            end_time = parse_time(section["ETime"])
            meeting_days = _extract_meeting_days(section)
            for day in meeting_days:
                if day in DAYS_OF_WEEK:
                    start_times_by_day[day].append(start_time)
                    end_times_by_day[day].append(end_time)

    # Remove empty lists
    start_times_by_day = {day: times for day, times in start_times_by_day.items() if times}
    end_times_by_day = {day: times for day, times in end_times_by_day.items() if times}

    if not start_times_by_day or not end_times_by_day:
        return {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}

    # For each day, find the start time of the earliest section and the end time of the latest section
    first_section_start_time = [min(times) for times in start_times_by_day.values()]
    last_section_end_time = [max(times) for times in end_times_by_day.values()]

    # Calculate the average start time and end time for the day over the course of the week
    avg_start_time = _average_time(first_section_start_time)
    avg_end_time = _average_time(last_section_end_time)

    # Calculate daily deviations from the average start time and end time, in hours
    start_time_deviations = [(t.hour + t.minute / 60) - (avg_start_time.hour + avg_start_time.minute / 60) for t in first_section_start_time]
    end_time_deviations = [(t.hour + t.minute / 60) - (avg_end_time.hour + avg_end_time.minute / 60) for t in last_section_end_time]

    # Calculate the sum of the absolute values of the deviations over the course of the week
    total_start_time_deviation = sum(abs(dev) for dev in start_time_deviations)
    total_end_time_deviation = sum(abs(dev) for dev in end_time_deviations)

    # Apply penalty per hour
    start_time_consistency_score = total_start_time_deviation * penalty_weight
    end_time_consistency_score = total_end_time_deviation * penalty_weight

    # Format scores to one decimal place
    start_time_consistency_score = round(start_time_consistency_score, 1)
    end_time_consistency_score = round(end_time_consistency_score, 1)

    return {"start_time_consistency_score": start_time_consistency_score, "end_time_consistency_score": end_time_consistency_score}

def _combined_score(combination: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Score a schedule for a combination of scores, including modality, days, gaps, and max sections per day.
    MODIFY THIS FUNCTION whenever a new score is added.  Add new score to combined_score calculation and return dictionary.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, int]: A dictionary of the score names and their values.
    """
    modality_score = _score_modality(combination)
    days_score = _score_days_on_campus(combination)
    gap_score = _score_gaps(combination)
    max_sections_score = _score_max_sections_per_day(combination)
    consistency_scores = _score_consistency(combination)
    # Add new score here

    combined_score = (
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score +
        config["weights"]["modality"] * modality_score +
        config["weights"].get("sections_per_day", 1) * max_sections_score +
        config["weights"].get("consistency_start_time", 1) * consistency_scores["start_time_consistency_score"] +
        config["weights"].get("consistency_end_time", 1) * consistency_scores["end_time_consistency_score"]
        # Add new score and the config weights here when expanding the scoring layer
    )

    # Format scores to one decimal place
    combined_score = round(combined_score, 1)

    return {
        "combined_score": combined_score,
        "days_score": days_score,
        "gap_score": gap_score,
        "modality_score": modality_score,
        "max_sections_score": max_sections_score,
        "start_time_consistency_score": consistency_scores["start_time_consistency_score"],
        "end_time_consistency_score": consistency_scores["end_time_consistency_score"],
        # Add new score and value here when expanding the scoring layer
    }

def score_combinations(combinations: List[List[Dict[str, Any]]]) -> List[Tuple[List[Dict[str, Any]], Dict[str, int]]]:
    '''
    Score a list of schedule combinations.

    Args:
        combinations (List[List[Dict[str, Any]]]): A list of schedule combinations.

    Returns:
        List[Tuple[List[Dict[str, Any]], Dict[str, int]]]: A list of tuples where each tuple contains a schedule combination and its scores.
    '''
    scored_combinations = []
    for combination in combinations:
        try:
            scores = _combined_score(combination)
            scored_combinations.append((combination, scores))
        except Exception as e:
            error_message = str(e)
            if 'score_combinations' not in errors:
                errors['score_combinations'] = set()
            if error_message not in errors['score_combinations']:
                errors['score_combinations'].add(error_message)
            logger.error(f"Error scoring combination: {e}")

    scored_combinations.sort(key=lambda x: x[1]["combined_score"])  # Sort by the combined score
    return scored_combinations

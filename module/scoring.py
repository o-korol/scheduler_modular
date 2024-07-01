"""
When adding a new scoring function, remember to add the new score to _combined_score and score_combinations functions in this module.
The header in print_summary and the title in plot_schedule should update automatically.
"""
from datetime import datetime, time
from typing import List, Dict, Tuple, Any
from . import utils
from .utils import parse_time, parse_time_range, time_difference_in_minutes
from .config import config

# Constants
DAYS_OF_WEEK = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']

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

def _extract_meeting_days(section: Dict[str, Any]) -> List[str]:
    """
    Extract section's meeting days.
    (Helper function for _score_max_sections_per_day, _score_days_on_campus, score_gaps, _score_consistency, and _extract_time_bounds.)

    Args:
        section (Dict[str, Any]): A dictionary representing a course section.

    Returns:
        List[str]: A list of meeting days, stripped of spaces.
    """
    if section["Mtg_Days"]: # If section has meeting days, return the list of days
        return [day.strip() for day in section["Mtg_Days"].split(',')]
    return [] # If section does not have meeting days (e.g., ONLIN section), return an empty list

@utils.time_function
def _score_max_sections_per_day(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule based on the maximum number of sections per day.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The penalty score for exceeding the maximum number of sections per day.
    """
    sections_per_day = {day: 0 for day in DAYS_OF_WEEK}  # Create and initialize a dictionary: keys are days of the week and values are number of sections that day
    max_sections_per_day = config.get("preferred_max_sections_per_day") # Get preferred number of days on campus
    penalty_per_excess_section = config.get("penalty_per_excess_section", 1)  # Get penalty value for each excessive section

    # Populate the dictionary
    for section in combination:  # For every section in a schedule
        meeting_days = _extract_meeting_days(section)  # Create a list of meeting days
        for day in meeting_days:  # For each of the meeting days
            if day in sections_per_day:  # If the day is one of the days in the week's dictionary (Mon-Sun)
                sections_per_day[day] += 1  # Increase the section count for that day by one in the dictionary

    excessive_sections_score = 0
    for day, section_count in sections_per_day.items():
        excess_sections = section_count - max_sections_per_day
        if excess_sections > 0:
            # Calculate penalty for excess sections
            excessive_sections_score += excess_sections * penalty_per_excess_section

    return excessive_sections_score

@utils.time_function
def _score_days_on_campus(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule for its ability to meet student's preference for the number of days on campus.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The penalty score for days on campus over the preferred number of days.
    """
    preferred_num_days = config["preferred_num_days"] # Get the number of days the student prefers to be on campus
    penalty_per_excess_day = config["penalty_per_excess_day"]  # Get penalty value for each excess day on campus
    days_on_campus = set() # Create a set of days on campus and populate it with loop below
    for section in combination:
        if section["Mtg_Days"]:
            meeting_days = _extract_meeting_days(section)
            days_on_campus.update(meeting_days) # Add days of the week that have not been seen before to the set (sets cannot contain duplicates)

    num_days = len(days_on_campus)
    excess_days = num_days - preferred_num_days

    day_score = max(0, excess_days * penalty_per_excess_day)  # Calculate penalty for excess days

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
    has_section_before = any(section["ETime"] <= break_start for section in day_sections)
    has_section_after = any(section["STime"] >= break_end for section in day_sections)

    if has_section_before and has_section_after:
        day_sections.append({
            "Name": "Mandatory Break",
            "STime": break_start,
            "ETime": break_end,
            "Mtg_Days": "Mandatory"
        })

# Do we want to pass penalty rate to this function or should we just pull it up from config inside this function?
def _score_gaps_per_day(day_sections: List[Dict[str, Any]], max_allowed_gap: int, penalty_per_gap_hour: int) -> int:
    """
    Score a day in a schedule for the duration of gaps between classes.
    (Helper function of _score_gaps.)

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections for the day that represents the schedule for the day.
        max_allowed_gap (int): Maximum allowed (penalty-free) gap, in minutes.
        penalty_per_gap_hour (int): Penalty per hour for gaps exceeding the maximum allowed gap.

    Returns:
        int: The day gap score.
    """
    day_gap_score = 0

    for i in range(1, len(day_sections)): # Is this list sorted by starting time?
        prev_section = day_sections[i - 1]
        curr_section = day_sections[i]

        prev_end_time = prev_section["ETime"]
        curr_start_time = curr_section["STime"]
        gap_minutes = time_difference_in_minutes(curr_start_time, prev_end_time)

        if gap_minutes > max_allowed_gap:
            gap_hours = round(gap_minutes / 60)
            day_gap_score += gap_hours * penalty_per_gap_hour # Penalty rate is defined in config

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
    penalty_per_gap_hour = gap_config["penalty_per_gap_hour"]

    day_sections_map = {day: [] for day in DAYS_OF_WEEK} # Create a dictionary: keys are days of the week and values are lists of sections for that day

    for section in combination:  # Loop through every section in a schedule
        if section["STime"] and section["ETime"]: # If section has start and end times, parse them
            start_time = parse_time(section["STime"])
            end_time = parse_time(section["ETime"])
            meeting_days = _extract_meeting_days(section) # If section has meeting days, turn them into a list
            if meeting_days:  # Ignore sections without meeting days
                for day in meeting_days: # Loop through each day in the meeting days list
                    if day in day_sections_map:  # If it is a valid day (Mon-Sun)
                        day_sections_map[day].append({ # Add section's info to the dictionary as a list (?)
                            "Name": section["Name"],
                            "STime": start_time,
                            "ETime": end_time,
                            "Mtg_Days": day
                        })

    for day, day_sections in day_sections_map.items():
        if day in ['M', 'W', 'F']:
            _add_mandatory_break(day_sections, mandatory_break_start, mandatory_break_end)

        day_sections.sort(key=lambda section: section["STime"]) # Sort sections by start time
        gap_score += _score_gaps_per_day(day_sections, max_allowed_gap, penalty_per_gap_hour) # Score gaps for the day and add them to the running total

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

# Testing
def _extract_time_bounds(combination: List[Dict[str, Any]]) -> Dict[str, Tuple[time, time]]:
    """
    Extract the earliest section start time and latest section end time for each day.
    (Helper function for _score_consistency and _score_availability.)

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, Tuple[time, time]]: A dictionary with days as keys and tuples of earliest start time and latest end time as values.
    """
    time_bounds_by_day = {day: (time.max, time.min) for day in DAYS_OF_WEEK}
    for section in combination:
        if section["STime"] and section["ETime"]:
            section_start = parse_time(section["STime"])
            section_end = parse_time(section["ETime"])
            meeting_days = _extract_meeting_days(section)
            for day in meeting_days:
                if day in DAYS_OF_WEEK:
                    current_earliest, current_latest = time_bounds_by_day[day]
                    new_earliest = min(current_earliest, section_start)
                    new_latest = max(current_latest, section_end)
                    time_bounds_by_day[day] = (new_earliest, new_latest)
    return {day: bounds for day, bounds in time_bounds_by_day.items() if bounds != (time.max, time.min)}

#Testing:  refactored with extract_time_bounds:  seems to work so far
@utils.time_function
def _score_consistency(combination: List[Dict[str, Any]]) -> Dict[str, float]:
    """
    Score a schedule based on the day-to-day consistency of start and end times.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, float]: A dictionary with scores for day-to-day start time consistency and end time consistency.
    """
    # Extract time bounds by day
    time_bounds_by_day = _extract_time_bounds(combination)
    if not time_bounds_by_day:
        return {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}

    # Create two lists, one holding the start time for all days of the week and one, holding the end times
    first_section_start_time = [bounds[0] for bounds in time_bounds_by_day.values()]
    last_section_end_time = [bounds[1] for bounds in time_bounds_by_day.values()]
    # Calculate the average start time and end time for the day over the course of the week
    avg_start_time = _average_time(first_section_start_time)
    avg_end_time = _average_time(last_section_end_time)

    # Calculate daily deviations from the average start time and end time, in hours
    penalty_weight = config["consistency_penalty_weight"]
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

# Testing
@utils.time_function
def _score_availability(combination: List[Dict[str, Any]], availability: Dict[str, List[str]], config: Dict[str, Any]) -> int:
    """
    Calculate the availability score for a given schedule.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.
        availability (Dict[str, List[str]]): A dictionary of user availability times.
        config (Dict[str, Any]): Configuration dictionary containing penalties and weights.

    Returns:
        int: The total availability penalty score.
    """
    # Helps deal with mock availability having keys that are fully spelled out days of the week, as opposed to just first letter(s)
    day_mapping = {
        "Monday": "M", "Tuesday": "T", "Wednesday": "W", "Thursday": "TH",
        "Friday": "F", "Saturday": "S", "Sunday": "SU"
    }

    # Map the availability days to their abbreviations
    mapped_availability = {day_mapping[day]: times for day, times in availability.items()}

    time_out_of_bounds = config["availability"]["time_out_of_bounds"]
    penalty_per_15_min = config["availability"]["penalty_per_15_min"]

    total_penalty = 0
    time_bounds_by_day = _extract_time_bounds(combination)

    for day, (section_start, section_end) in time_bounds_by_day.items():
        if day in mapped_availability and len(mapped_availability[day]) == 1:
            # Single block availability: simple boundary check
            avail_start, avail_end = parse_time_range(mapped_availability[day][0])
            if section_start < avail_start:
                out_of_bounds_minutes = time_difference_in_minutes(avail_start, section_start)
                penalty_units = (out_of_bounds_minutes + time_out_of_bounds - 1) // time_out_of_bounds
                total_penalty += penalty_units * penalty_per_15_min
            if section_end > avail_end:
                out_of_bounds_minutes = time_difference_in_minutes(section_end, avail_end)
                penalty_units = (out_of_bounds_minutes + time_out_of_bounds - 1) // time_out_of_bounds
                total_penalty += penalty_units * penalty_per_15_min

    return total_penalty

@utils.time_function
def _combined_score(combination: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Score a schedule for a combination of scores, including modality, days, gaps, and max sections per day.
    MODIFY THIS FUNCTION whenever a new score is added. Add new score to combined_score calculation and return dictionary.

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
    availability_score = _score_availability(combination, config["user_availability"], config) # Testing

    combined_score = (
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score +
        config["weights"]["modality"] * modality_score +
        config["weights"].get("sections_per_day", 1) * max_sections_score +
        config["weights"].get("consistency_start_time", 1) * consistency_scores["start_time_consistency_score"] +
        config["weights"].get("consistency_end_time", 1) * consistency_scores["end_time_consistency_score"] +
        config["weights"].get("availability", 1) * availability_score # Testing
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
        "availability_score": availability_score # Testing
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

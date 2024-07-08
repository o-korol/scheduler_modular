"""
When adding a new scoring function, remember to add the new score to _combined_score and score_combinations functions in this module.
The header in print_summary and the title in plot_schedule should update automatically.
"""
from datetime import time
from typing import List, Dict, Tuple, Any

from module.config import config
from module import utils
from module.utils import (parse_time, parse_time_range, time_difference_in_minutes,
                          errors, logger, ConfigurationError)


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

    Note:
        this function will need to be modified to handle "no preference" option,
        treating it just as if the modality preference are met condition.
    """
    try:
        # Get student's modality preferences from config
        modality_preferences = config["modality_preferences"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError("Missing critical configuration: 'modality_preferences'")

    modality_score = 0

    for section in combination:
        # Get course name from section name
        course_name = '-'.join(section["Name"].split('-')[:2])
        section_modality = section["Method"]
        # Get preferred modality for the course from modality preferences
        preferred_modality = modality_preferences.get(course_name)

        if preferred_modality and section_modality != preferred_modality:
            modality_score += 1

    return modality_score


def _extract_meeting_days(section: Dict[str, Any]) -> List[str]:
    """
    Extract section's meeting days.
    (Helper function for _score_max_sections_per_day, _score_days_on_campus,
    score_gaps, _score_consistency, and _extract_time_bounds.)

    Args:
        section (Dict[str, Any]): A dictionary representing a course section.

    Returns:
        List[str]: A list of meeting days, stripped of spaces.
    """
    if section["Mtg_Days"]:  # If section has meeting days, return the list of days
        return [day.strip() for day in section["Mtg_Days"].split(',')]
    return []  # If section does not have meeting days (e.g., ONLIN), return an empty list


@utils.time_function
def _score_max_sections_per_day(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule based on the maximum number of sections per day.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The penalty score for exceeding the maximum number of sections per day.
    """
    # Create and initialize a dictionary: keys are days of the week and values are number of sections that day
    sections_per_day = {day: 0 for day in DAYS_OF_WEEK}

    try:
        # Get preferred max number of sections per day
        max_sections_per_day = config["preferred_max_sections_per_day"]
        # Get penalty value for each additional section
        penalty_per_excess_section = config["penalty_per_excess_section"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError(f"Missing critical configuration: {e.args[0]}")

    # Populate the dictionary
    for section in combination:  # For every section in a schedule
        meeting_days = _extract_meeting_days(section)  # Create a list of meeting days
        # For each of the meeting days, if the day is in the dictionary,
        # increase section count by one for that day
        for day in meeting_days:
            if day in sections_per_day:
                sections_per_day[day] += 1

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
    try:
        # Get preferred max number of sections per day
        preferred_num_days = config["preferred_num_days"]
        # Get penalty value for each additional section
        penalty_per_excess_day = config["penalty_per_excess_day"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError(f"Missing critical configuration: {e.args[0]}")

    days_on_campus = set()  # Create a set of days on campus
    for section in combination:
        if section["Mtg_Days"]:
            meeting_days = _extract_meeting_days(section)
            # Add days of the week that have not been seen before to the set
            # (only new days are added because sets cannot contain duplicates)
            days_on_campus.update(meeting_days)

    num_days = len(days_on_campus)
    excess_days = num_days - preferred_num_days

    # Calculate penalty for excess days
    day_score = max(0, excess_days * penalty_per_excess_day)

    return day_score


def _add_mandatory_break(day_sections: List[Dict[str, Any]], break_start: time, break_end: time) -> None:
    """
    Add a mandatory break (College Hour) on MWF, but only if there are sections schedules for before and after.
    (Helper function of _score_gaps.)

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections that represents the schedule for the day.
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


def _score_gaps_per_day(day_sections: List[Dict[str, Any]]) -> int:
    """
    Score a day in a schedule for the duration of gaps between classes.
    (Helper function of _score_gaps.)

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections that represents the schedule for the day.

    Returns:
        int: The day gap score.

    Note:
        it may be better to pass max_allowed_gap and penalty_per_gap_hour as arguments.
        See _scoring_v8 for that version of the function.  If revert, will need to rewrite the tests.
    """
    try:
        # Get preferred max number of sections per day
        max_allowed_gap = config["gap_weights"]["max_allowed_gap"]
        # Get penalty value for each additional section
        penalty_per_gap_hour = config["gap_weights"]["penalty_per_gap_hour"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError(f"Missing critical configuration: {e.args[0]}")

    day_gap_score = 0

    for i in range(1, len(day_sections)):  # Is this list sorted by starting time?
        prev_section = day_sections[i - 1]
        curr_section = day_sections[i]

        prev_end_time = prev_section["ETime"]
        curr_start_time = curr_section["STime"]
        gap_minutes = time_difference_in_minutes(curr_start_time, prev_end_time)

        if gap_minutes > max_allowed_gap:
            gap_hours = round(gap_minutes / 60)
            day_gap_score += gap_hours * penalty_per_gap_hour

    return day_gap_score


def _group_and_sort_sections_by_day(combination: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group all sections that meet on the same day and then sort them by start time in ascending order.
    (Helper function for _score_gaps and _score_location_change.)

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, List[Dict[str, Any]]]: A dictionary where keys are days of the week
        and values are lists of sections for that day, sorted by start time.
    """
    day_sections_map = {day: [] for day in DAYS_OF_WEEK}

    for section in combination:
        if section["STime"] and section["ETime"]:
            start_time = parse_time(section["STime"])
            end_time = parse_time(section["ETime"])
            meeting_days = _extract_meeting_days(section)
            if meeting_days:
                for day in meeting_days:
                    if day in day_sections_map:
                        day_sections_map[day].append({
                            "Name": section["Name"],
                            "STime": start_time,
                            "ETime": end_time,
                            "Mtg_Days": day
                        })

    for day, day_sections in day_sections_map.items():
        day_sections.sort(key=lambda section: section["STime"])

    return day_sections_map


def _score_gaps(combination: List[Dict[str, Any]]) -> int:
    """
    Score a schedule for the duration of gaps between classes.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The gap score.
    """
    try:
        mandatory_break_start = config["gap_weights"]["mandatory_break_start"]
        mandatory_break_end = config["gap_weights"]["mandatory_break_end"]
    except KeyError as e:
        raise ConfigurationError(f"Missing critical configuration: {e.args[0]}")

    mandatory_break_start = parse_time(mandatory_break_start)
    mandatory_break_end = parse_time(mandatory_break_end)

    gap_score = 0

    day_sections_map = _group_and_sort_sections_by_day(combination)

    for day, day_sections in day_sections_map.items():
        if day in ['M', 'W', 'F']:
            _add_mandatory_break(day_sections, mandatory_break_start, mandatory_break_end)
        gap_score += _score_gaps_per_day(day_sections)

    return gap_score


def _score_location_change_by_day(day_sections: List[Dict[str, Any]]) -> int:
    """
    Score a day in a schedule for location changes between sections.

    Args:
        day_sections (List[Dict[str, Any]]): A list of sections that represents the schedule for the day.

    Returns:
        int: The day location change score.
    """
    try:
        # Get the minimum time gap between sections that permits changing location
        minimum_permissible_gap = config["location_change"]["minimum_permissible_gap"]
        # Get the penalty for adjacent sections meeting in different locations
        # if the gap between the sections is shorter than minimum gap (larger penalty)
        unacceptable_gap_penalty = config["location_change"]["unacceptable_gap_penalty"]
        # Get the penalty for adjacent sections meeting in different locations
        # if the gap between the sections is longer than minimum gap (smaller penalty)
        acceptable_gap_penalty = config["location_change"]["acceptable_gap_penalty"]
    except KeyError as e:
        # Handle missing keys
        raise ConfigurationError(f"Missing critical configuration: {e.args[0]}")

    location_change_score_day = 0

    for i in range(1, len(day_sections)):
        prev_section = day_sections[i - 1]
        curr_section = day_sections[i]

        # Skip sections without locations
        if "Location" not in prev_section or "Location" not in curr_section:
            continue

        prev_end_time = prev_section["ETime"]
        curr_start_time = curr_section["STime"]
        gap_minutes = time_difference_in_minutes(curr_start_time, prev_end_time)

        if prev_section["Location"] != curr_section["Location"]:
            gap_hours = gap_minutes / 60
            if gap_hours < minimum_permissible_gap:
                location_change_score_day += unacceptable_gap_penalty
            else:
                location_change_score_day += acceptable_gap_penalty

    return int(location_change_score_day)


def _score_location_change(combination: List[Dict[str, Any]]) -> int:
    """
    Score the entire schedule for location changes between sections, across all days of the week.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The total location change score.
    """
    day_sections_map = _group_and_sort_sections_by_day(combination)
    location_change_score = 0

    for day, day_sections in day_sections_map.items():
        location_change_score += _score_location_change_by_day(day_sections)

    return location_change_score


def _average_time(times: List[time]) -> time:
    """
    Calculate the average time from a list of times.
    (Helper function of _score_consistency.)

    Args:
        times (List[time]): A list of time objects.

    Returns:
        time: The average time.

    Note:
        This function does not handle correctly times spanning across midnight.
    """
    total_minutes = sum(t.hour * 60 + t.minute for t in times)
    avg_minutes = total_minutes // len(times)
    avg_hour = avg_minutes // 60
    avg_minute = avg_minutes % 60
    return time(avg_hour, avg_minute)


def _extract_time_bounds(combination: List[Dict[str, Any]]) -> Dict[str, Tuple[time, time]]:
    """
    Extract the earliest section start time and latest section end time for each day.
    (Helper function for _score_consistency and _score_availability.)

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        Dict[str, Tuple[time, time]]: A dictionary with days as keys and tuples
        of earliest start time and latest end time as values.
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

    return {
        day: bounds
        for day, bounds in time_bounds_by_day.items()
        if bounds != (time.max, time.min)
    }


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

    try:
        # Get consistency penalty weight
        penalty_weight = config["consistency_penalty_weight"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError("Missing critical configuration: 'consistency_penalty_weight'")

    if not time_bounds_by_day:
        return {"start_time_consistency_score": 0.0, "end_time_consistency_score": 0.0}

    # Create two lists, one holding the start time for all days of the week
    # and one, for holding the end times
    first_section_start_time = [bounds[0] for bounds in time_bounds_by_day.values()]
    last_section_end_time = [bounds[1] for bounds in time_bounds_by_day.values()]

    # Calculate the average start time and end time for the day over the course of the week
    avg_start_time = _average_time(first_section_start_time)
    avg_end_time = _average_time(last_section_end_time)

    # Calculate daily deviations from the average start time and end time, in hours
    def time_to_hours(time):
        """Helper function to convert time to hours.
        Consider moving it to utils, since something similar is also used in plotting module."""
        return time.hour + time.minute / 60

    # Calculate start time deviations
    avg_start_time_in_hours = time_to_hours(avg_start_time)
    start_time_deviations = [
        time_to_hours(t) - avg_start_time_in_hours
        for t in first_section_start_time
    ]

    # Calculate end time deviations
    avg_end_time_in_hours = time_to_hours(avg_end_time)
    end_time_deviations = [
        time_to_hours(t) - avg_end_time_in_hours
        for t in last_section_end_time
    ]

    # Calculate the sum of the absolute values of the deviations over the course of the week
    total_start_time_deviation = sum(abs(dev) for dev in start_time_deviations)
    total_end_time_deviation = sum(abs(dev) for dev in end_time_deviations)

    # Apply penalty per hour
    start_time_consistency_score = total_start_time_deviation * penalty_weight
    end_time_consistency_score = total_end_time_deviation * penalty_weight

    # Format scores to one decimal place
    start_time_consistency_score = round(start_time_consistency_score, 1)
    end_time_consistency_score = round(end_time_consistency_score, 1)

    return {
        "start_time_consistency_score": start_time_consistency_score,
        "end_time_consistency_score": end_time_consistency_score
    }


@utils.time_function
def _score_availability(combination: List[Dict[str, Any]], availability: Dict[str, List[str]]) -> float:
    """
    Calculate the availability score for a given schedule.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.
        availability (Dict[str, List[str]]): A dictionary of user availability times.

    Returns:
        float: The total availability penalty score.
    """
    try:
        # Get availability penalty weight
        penalty_per_hour = config["availability_penalty_per_hour"]
    except KeyError:
        # Handle missing keys
        raise ConfigurationError("Missing critical configuration: 'availability_penalty_per_hour'")

    total_penalty = 0.0
    # Returns dictionary:  keys are days and values are tuples of end time and start time
    time_bounds_by_day = _extract_time_bounds(combination)

    for day, (first_section_start, last_section_end) in time_bounds_by_day.items():
        if day in availability and len(availability[day]) == 1:
            # Single block availability: simple boundary check
            avail_start, avail_end = parse_time_range(availability[day][0])

            if first_section_start < avail_start:
                out_of_bounds_minutes = time_difference_in_minutes(avail_start, first_section_start)
                total_penalty += (out_of_bounds_minutes / 60) * penalty_per_hour

            if last_section_end > avail_end:
                out_of_bounds_minutes = time_difference_in_minutes(last_section_end, avail_end)
                total_penalty += (out_of_bounds_minutes / 60) * penalty_per_hour

        elif day not in availability or len(availability[day]) == 0:
            # No availability for this day: entire duration is out of bounds
            # (_extract_time_bounds function takes care of multiple sections per day)
            out_of_bounds_minutes = time_difference_in_minutes(last_section_end, first_section_start)
            total_penalty += (out_of_bounds_minutes / 60) * penalty_per_hour

    total_penalty = round(total_penalty, 1)
    return total_penalty


def _score_enrollment_balancing(combination: List[Dict[str, Any]]) -> int:
    """
    Calculate the enrollment balancing score for a schedule combination.

    Args:
        combination (List[Dict[str, Any]]): A list of course sections that represents a schedule.

    Returns:
        int: The enrollment balancing score.
    """
    try:
        # Get the penalty rate from config
        penalty_rate = config["enrollment_balancing_penalty_rate"]
    except KeyError:
         # Handle missing keys
        raise ConfigurationError("Missing critical configuration: 'enrollment_balancing_penalty_rate'")

    sum_fraction_full_deviation = sum(
        section.get('Fraction_Full_Deviation', 0)
        for section in combination
    )
    enrollment_balancing_score = sum_fraction_full_deviation * penalty_rate
    enrollment_balancing_score = round(enrollment_balancing_score, 1)

    return enrollment_balancing_score


@utils.time_function
def _combined_score(combination: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Score a schedule for a combination of scores, including modality, days, gaps, etc.
    MODIFY THIS FUNCTION whenever a new score is added:
    add new score to combined_score calculation and return dictionary.

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
    availability_score = _score_availability(combination, config["user_availability"])
    enrollment_balancing_score = _score_enrollment_balancing(combination)
    location_change_score = _score_location_change(combination)

    combined_score = (
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score +
        config["weights"]["modality"] * modality_score +
        config["weights"].get("sections_per_day", 1) * max_sections_score +
        config["weights"].get("consistency_start_time", 1) * consistency_scores["start_time_consistency_score"] +
        config["weights"].get("consistency_end_time", 1) * consistency_scores["end_time_consistency_score"] +
        config["weights"].get("availability", 1) * availability_score +
        config["weights"].get("enrollment_balancing", 1) * enrollment_balancing_score +
        config["weights"].get("location_change", 1) * location_change_score
        # Add new scores and their weights here, after a '+'
    )

    combined_score = round(combined_score, 1)

    return {
        "combined_score": combined_score,
        "days_score": days_score,
        "gap_score": gap_score,
        "modality_score": modality_score,
        "max_sections_score": max_sections_score,
        "start_time_consistency_score": consistency_scores["start_time_consistency_score"],
        "end_time_consistency_score": consistency_scores["end_time_consistency_score"],
        "availability_score": availability_score,
        "enrollment_balancing_score": enrollment_balancing_score,
        "location_change_score": location_change_score,
        # Add new scores here
    }


@utils.time_function
def score_combinations(
    combinations: List[List[Dict[str, Any]]]
) -> List[Tuple[List[Dict[str, Any]], Dict[str, int]]]:
    '''
    Score a list of schedule combinations.

    Args:
        combinations (List[List[Dict[str, Any]]]): A list of schedule combinations.

    Returns:
        List[Tuple[List[Dict[str, Any]], Dict[str, int]]]: A list of tuples
        where each tuple contains a schedule combination and its scores.
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

    # Sort by the combined score
    scored_combinations.sort(key=lambda x: x[1]["combined_score"])

    return scored_combinations

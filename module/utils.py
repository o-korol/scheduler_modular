from datetime import datetime
import functools
import logging
import time
from typing import List, Dict, Tuple, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

execution_times = {}
errors = {}
total_execution_time = 0


def time_function(func):
    """
    Decorator to measure the execution time of a function and store the results.

    Args:
        func (function): The function to be wrapped and timed.

    Returns:
        function: The wrapped function with timing functionality.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        global total_execution_time
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            func_name = func.__name__
            error_message = str(e)
            section_info = ""
            if "sections" in kwargs and kwargs['sections']:
                section_info = f"in section {kwargs['sections'][0]['Name']}"
            detailed_message = f"{error_message} {section_info}"
            if func_name not in errors:
                errors[func_name] = set()
            if detailed_message not in errors[func_name]:
                errors[func_name].add(detailed_message)

            logger.error(f"{func_name}: {detailed_message}")
            raise e
        end_time = time.time()
        elapsed_time = end_time - start_time
        total_execution_time += elapsed_time
        func_name = func.__name__

        if func_name not in execution_times:
            execution_times[func_name] = []
        execution_times[func_name].append(elapsed_time)

        logger.debug(f"{func_name} executed in {elapsed_time:.4f} seconds")
        return result
    return wrapper


def parse_time(time_str):
    """
    Parse a time string into a time object.

    Args:
        time_str (str): The time string to be parsed.

    Returns:
        datetime.time: The parsed time object.
    """
    return datetime.strptime(time_str, '%I:%M %p').time() if time_str else None


def parse_date(date_str):
    """
    Parse a date string into a datetime object.

    Args:
        date_str (str): The date string to be parsed.

    Returns:
        datetime: The parsed datetime object.
    """
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') if date_str else None


def parse_time_range(time_range: str) -> Tuple[time, time]:
    """
    Parse a time range string into a tuple of time objects.

    Args:
        time_range (str): The time range string to be parsed.

    Returns:
        tuple: A tuple containing the start and end time objects.
    """
    start_str, end_str = time_range.split('-')
    start_time = datetime.strptime(start_str.strip(), "%I:%M %p").time()
    end_time = datetime.strptime(end_str.strip(), "%I:%M %p").time()
    return start_time, end_time


def time_difference_in_minutes(t1: time, t2: time) -> int:
    """
    Calculate the difference between two times in minutes.

    Args:
        t1 (time): The first time.
        t2 (time): The second time.

    Returns:
        int: The difference in minutes.
    """
    datetime1 = datetime.combine(datetime.min, t1)
    datetime2 = datetime.combine(datetime.min, t2)
    return int((datetime1 - datetime2).total_seconds() // 60)


def parse_section_times(section):
    """
    Parse and add parsed time, date, and days to a section.
    (Helper function of has_time_conflict)

    Args:
        section (dict): The section dictionary to be parsed.
    """
    if 'parsed_start_time' not in section:
        section['parsed_start_time'] = parse_time(section['STime'])
    if 'parsed_end_time' not in section:
        section['parsed_end_time'] = parse_time(section['ETime'])
    if 'parsed_start_date' not in section:
        section['parsed_start_date'] = parse_date(section['SDate'])
    if 'parsed_end_date' not in section:
        section['parsed_end_date'] = parse_date(section['EDate'])
    if 'parsed_days' not in section:
        section['parsed_days'] = (set(section['Mtg_Days'].split(', '))
                                  if section['Mtg_Days'] else set())


def check_time_conflict(section1, section2):
    """
    Check if two sections have a time conflict on common meeting days.
    (Helper function of has_time_conflict)

    Args:
        section1 (dict): The first section dictionary.
        section2 (dict): The second section dictionary.

    Returns:
        bool: True if there is a time conflict, False otherwise.
    """
    # Find common meeting days: find intersection of meeting days sets
    common_days = section1['parsed_days'].intersection(section2['parsed_days'])

    # Abort if no common days
    if not common_days:
        return False

    # Abort if sections do not have start time
    if (section1['parsed_start_time'] is None or
        section2['parsed_start_time'] is None):
        return False

    # Check if there is a time overlap between the two sections
    # Check both ways, just in case the sections are not sorted by time yet
    has_conflict = (
        section1['parsed_start_time'] < section2['parsed_end_time'] and
        section1['parsed_end_time'] > section2['parsed_start_time']
    )

    # Return True if there is time conflict
    return has_conflict


@time_function
def has_time_conflict(sections, new_section=None):
    """
    Checks whether two sections have a time conflict. A critical part of the scheduling engine.

    Args:
        sections (list): A list of section dictionaries.
        new_section (dict, optional): A new section to check against the list. Defaults to None.

    Returns:
        bool: True if there is a time conflict, False otherwise.
    """
    for section in sections:
        parse_section_times(section)

    if new_section:
        parse_section_times(new_section)
        for section in sections:
            if check_time_conflict(section, new_section):
                return True
        return False

    # Assign fake sorting time (midnight) to sections without meeting time
    min_time = parse_time('12:00 AM')

    # Sort sections by start date, end date, and start time
    sections.sort(
        key=lambda x: (
            x['parsed_start_date'],
            x['parsed_end_date'],
            x['parsed_start_time'] if x['parsed_start_time'] is not None else min_time
        )
    )

    for i, s1 in enumerate(sections):
        for s2 in sections[i + 1:]:
            if s1['parsed_end_date'] < s2['parsed_start_date']:
                break
            if check_time_conflict(s1, s2):
                return True
    return False


@time_function
def sort_combination(combination):
    """
    Sort a combination of sections by meeting days and start times.

    Args:
        combination (list): A list of section dictionaries.

    Returns:
        list: The sorted list of sections.
    """
    day_to_number = {'M': 0, 'T': 1, 'W': 2, 'TH': 3, 'F': 4, 'S': 5, 'SU': 6}

    def sort_key(section):
        if not section["Mtg_Days"]:
            return (7, section["Name"])  # Sort sections with no meeting days to the end

        # Get the first meeting day
        first_day = section["Mtg_Days"].split(', ')[0]
        # Map the day to its corresponding number, default to 8 if not found
        day_number = day_to_number.get(first_day, 8)
        # Parse the start time, default to '12:00 AM' if missing
        start_time = parse_time(section["STime"]) if section["STime"] else parse_time('12:00 AM')
        # Return a tuple (day_number, start_time) for sorting
        return (day_number, start_time)

    # Sort the combination using the sort_key
    return sorted(combination, key=sort_key)


@time_function
def print_summary(scored_combinations):
    """
    Print a summary of scored schedule combinations.

    Args:
        scored_combinations (list): A list of tuples containing combinations and their scores.
    """
    def format_section(section):
        section_name = section["Name"]
        meeting_days = section["Mtg_Days"]

        meeting_days_str = (
            meeting_days
            if meeting_days
            else f"{section['Method']} - No specified meeting times"
        )

        meeting_times = (
            f"{section['STime']} - {section['ETime']}"
            if section['STime'] and section['ETime']
            else ""
        )
        return f"{section_name} ({meeting_days_str} {meeting_times})"

    def print_combination(combination, option_number, scores):
        sorted_combination = sort_combination(combination)
        # Generate header dynamically,
        # from the dictionary of scores generated by _combined_score function
        # (scores have names like availability_score;
        # in the title they are changed to Availability Score)
        header = (
            ", ".join(
                [
                    f"{key.replace('_', ' ').title()} = {value}"
                    for key, value in scores.items()
                ]
            )
        )

        print(f"Option {option_number}: {header}")
        for section in sorted_combination:
            print(format_section(section))
        print()

    print("Generated valid schedule combinations:")

    if len(scored_combinations) > 100:
        print("BEST 50 COMBINATIONS:")
        for i, (combination, scores) in enumerate(scored_combinations[:50], start=1):
            print_combination(combination, i, scores)

        print("WORST 50 COMBINATIONS:")
        for i, (combination, scores) in enumerate(scored_combinations[-50:], start=len(scored_combinations)-49):
            print_combination(combination, i, scores)
    else:
        for i, (combination, scores) in enumerate(scored_combinations, start=1):
            print_combination(combination, i, scores)


def print_execution_summary():
    """
    Print a summary of execution times for timed functions.
    """
    print("\nExecution Time Summary:")
    for func_name, times in execution_times.items():
        total_time = sum(times)
        avg_time = total_time / len(times)
        num_loops = len(times)
        print(
            f"{func_name}: Total time = {total_time:.4f} seconds, "
            f"Average time per loop = {avg_time:.4f} seconds, "
            f"Loops = {num_loops}"
        )


def print_error_summary():
    """
    Print a summary of errors encountered during function executions.
    """
    print("\nError Summary:")
    for func_name, error_set in errors.items():
        print(f"{func_name}: {len(error_set)} unique errors")
        for error_message in error_set:
            print(f"  {error_message}")


class ConfigurationError(Exception):
    """Custom exception for configuration errors."""
    pass

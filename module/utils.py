from datetime import datetime
import functools
import time
import pandas as pd
import logging
# from .scoring import combined_score_dict  # Testing # Import the new function # Not needed here if print functions are moved to utils_print to avoid circular imports

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

execution_times = {}
errors = {}
total_execution_time = 0

def time_function(func):
    """Decorator to measure the execution time of a function and store the results."""
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

@time_function
def parse_time(time_str):
    return datetime.strptime(time_str, '%I:%M %p').time()

@time_function
def group_sections(df):
    groups = {}
    coreq_df = df[pd.notna(df['Coreq_Sections']) | pd.notna(df['Coreq_Course'])]
    non_coreq_df = df[pd.isna(df['Coreq_Sections']) & pd.isna(df['Coreq_Course'])]

    for _, row in non_coreq_df.iterrows():
        key = (row['Course_Name'], row['STime'], row['ETime'], row['Mtg_Days'])
        if key not in groups:
            groups[key] = []
        groups[key].append(row['Name'])

    grouped_df = []
    for group, names in groups.items():
        course_name, s_time, e_time, mtg_days = group
        group_name = ', '.join(names)
        example_row = non_coreq_df[non_coreq_df['Name'] == names[0]].iloc[0].copy()
        example_row['Name'] = group_name
        grouped_df.append(example_row)

    grouped_df = pd.DataFrame(grouped_df)

    final_df = pd.concat([grouped_df, coreq_df], ignore_index=True)
    return final_df

def parse_time(time_str):
    return datetime.strptime(time_str, '%I:%M %p').time() if time_str else None

def parse_date(date_str):
    return datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S') if date_str else None

@time_function
def has_time_conflict(sections, new_section=None):
    for section in sections:
        if 'parsed_start_time' not in section:
            section['parsed_start_time'] = parse_time(section['STime'])
        if 'parsed_end_time' not in section:
            section['parsed_end_time'] = parse_time(section['ETime'])
        if 'parsed_start_date' not in section:
            section['parsed_start_date'] = parse_date(section['SDate'])
        if 'parsed_end_date' not in section:
            section['parsed_end_date'] = parse_date(section['EDate'])
        if 'parsed_days' not in section:
            section['parsed_days'] = set(section['Mtg_Days'].split(', ')) if section['Mtg_Days'] else set()

    if new_section:
        if 'parsed_start_time' not in new_section:
            new_section['parsed_start_time'] = parse_time(new_section['STime'])
        if 'parsed_end_time' not in new_section:
            new_section['parsed_end_time'] = parse_time(new_section['ETime'])
        if 'parsed_start_date' not in new_section:
            new_section['parsed_start_date'] = parse_date(new_section['SDate'])
        if 'parsed_end_date' not in new_section:
            new_section['parsed_end_date'] = parse_date(new_section['EDate'])
        if 'parsed_days' not in new_section:
            new_section['parsed_days'] = set(new_section['Mtg_Days'].split(', ')) if new_section['Mtg_Days'] else set()

        for section in sections:
            common_days = section['parsed_days'].intersection(new_section['parsed_days'])
            if common_days:
                if section['parsed_start_time'] is None or new_section['parsed_start_time'] is None:
                    continue
                if not (section['parsed_end_time'] <= new_section['parsed_start_time'] or section['parsed_start_time'] >= new_section['parsed_end_time']):
                    return True
        return False
    else:
        min_time = datetime.strptime('12:00 AM', '%I:%M %p').time()

        sections.sort(key=lambda x: (x['parsed_start_date'], x['parsed_end_date'], x['parsed_start_time'] if x['parsed_start_time'] is not None else min_time))
        for i, s1 in enumerate(sections):
            for s2 in sections[i + 1:]:
                if s1['parsed_end_date'] < s2['parsed_start_date']:
                    break
                common_days = s1['parsed_days'].intersection(s2['parsed_days'])
                if common_days:
                    if s1['parsed_start_time'] is None or s2['parsed_start_time'] is None:
                        continue
                    if not (s1['parsed_end_time'] <= s2['parsed_start_time'] or s1['parsed_start_time'] >= s2['parsed_end_time']):
                        return True
        return False

@time_function
def sort_combination(combination):
    day_to_number = {'M': 0, 'T': 1, 'W': 2, 'TH': 3, 'F': 4, 'S': 5, 'SU': 6}

    def sort_key(section):
        if not section["Mtg_Days"]:
            return (7, section["Name"])

        first_day = section["Mtg_Days"].split(', ')[0]
        day_number = day_to_number.get(first_day, 8)
        start_time = datetime.strptime(section["STime"], '%I:%M %p').time() if section["STime"] else datetime.strptime('12:00 AM', '%I:%M %p').time()
        return (day_number, start_time)

    return sorted(combination, key=sort_key)

@time_function
def print_summary(scored_combinations):
    def format_section(section):
        section_name = section["Name"]
        meeting_days = section["Mtg_Days"]
        meeting_days_str = meeting_days if meeting_days else f"{section['Method']} - No specified meeting times"
        meeting_times = f"{section['STime']} - {section['ETime']}" if section['STime'] and section['ETime'] else ""
        return f"  {section_name} ({meeting_days_str} {meeting_times})"

    def print_combination(combination, option_number, scores):
        sorted_combination = sort_combination(combination)
        header = ", ".join([f"{key.replace('_', ' ').title()} = {value}" for key, value in scores.items()])
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
    print("\nExecution Time Summary:")
    for func_name, times in execution_times.items():
        total_time = sum(times)
        avg_time = total_time / len(times)
        num_loops = len(times)
        print(f"{func_name}: Total time = {total_time:.4f} seconds, Average time per loop = {avg_time:.4f} seconds, Loops = {num_loops}")

def print_error_summary():
    print("\nError Summary:")
    for func_name, error_set in errors.items():
        print(f"{func_name}: {len(error_set)} unique errors")
        for error_message in error_set:
            print(f"  {error_message}")

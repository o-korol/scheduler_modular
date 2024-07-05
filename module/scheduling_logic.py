from itertools import product
from typing import List, Dict, Any
from . import utils
from .database_operations import retrieve_section_info
from .utils import has_time_conflict

def get_coreqs(section: Dict[str, Any]) -> List[str]:
    """
    Get corequisite section(s) for a given section.

    Args:
        section (dict): A dictionary representing a course section.

    Returns:
        list: A list of corequisite sections.
    """
    coreqs = section.get('Coreq_Sections', '')
    return [coreq.strip() for coreq in coreqs.split(',')] if coreqs else []

def fetch_coreq_section(coreq: str, cursor: Any, coreq_cache: Dict[str, Any], section_cache: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Fetch corequisite section details from cache or database.

    Args:
        coreq (str): The corequisite section name.
        cursor (Any): Database cursor to execute queries.
        coreq_cache (Dict[str, Any]): Cache for corequisite sections.
        section_cache (Dict[str, Any]): Cache for section information.

    Returns:
        List[Dict[str, Any]]: The corequisite section details.
    """
    if coreq not in coreq_cache:
        coreq_course = coreq.rsplit('-', 1)[0]
        coreq_df, _ = retrieve_section_info(cursor, [coreq_course], section_cache)
        coreq_cache[coreq] = coreq_df[coreq_df['Name'].str.strip().str.upper() == coreq].to_dict('records')
    return coreq_cache[coreq]

def handle_coreq_error(e: Exception, section_name: str):
    """
    Handle corequisite error by logging the error message.

    Args:
        e (Exception): The exception raised.
        section_name (str): The name of the section that caused the error.
    """
    error_message = str(e)
    detailed_message = f"{error_message} in section {section_name}"
    if 'add_coreqs_to_combination' not in utils.errors:
        utils.errors['add_coreqs_to_combination'] = set()
    utils.errors['add_coreqs_to_combination'].add(detailed_message)

@utils.time_function
def add_coreqs_to_combination(combination: List[Dict[str, Any]], cursor: Any, coreq_cache: Dict[str, Any], section_cache: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
    """
    Add corequisite sections to a given combination of sections.

    Args:
        combination (list): A list of sections representing a combination.
        cursor (Any): Database cursor to execute queries.
        coreq_cache (Dict[str, Any]): Cache for corequisite sections.
        section_cache (Dict[str, Any]): Cache for section information.

    Returns:
        list: A list of extended combinations including corequisites, or an empty list if no extension is possible.
    """
    coreq_names = set(section['Name'].strip() for section in combination)
    processed_coreqs = set()
    provisional_combinations = [combination.copy()]

    for section in combination:
        coreqs = get_coreqs(section)
        new_combinations = []

        for coreq in coreqs:
            coreq = coreq.strip().upper()
            if coreq in coreq_names or coreq in processed_coreqs:
                continue

            try:
                coreq_section = fetch_coreq_section(coreq, cursor, coreq_cache, section_cache)
                if not coreq_section:
                    continue

                for provisional_combination in provisional_combinations:
                    temp_combination = provisional_combination.copy()
                    temp_combination.append(coreq_section[0])

                    if not has_time_conflict(provisional_combination, coreq_section[0]):
                        new_combinations.append(temp_combination)
                        coreq_names.add(coreq_section[0]['Name'])
                        processed_coreqs.add(coreq)
            except Exception as e:
                handle_coreq_error(e, section['Name'])

        if not new_combinations and coreqs:
            return []
        provisional_combinations = new_combinations or provisional_combinations

    return provisional_combinations

@utils.time_function
def generate_combinations_with_coreqs(cursor: Any, df: Any, section_cache: Dict[str, Any]) -> List[List[Dict[str, Any]]]:
    """
    Generate valid section combinations including corequisite sections.

    Args:
        cursor: Database cursor to execute queries.
        df (DataFrame): DataFrame containing course sections.
        section_cache (dict): Cache to store retrieved section information.

    Returns:
        list: A list of valid section combinations including corequisites.
    """
    if df.empty:
        return []

    courses = df['Course_Name'].unique()
    sections_by_course = {course: df[df['Course_Name'] == course].to_dict('records') for course in courses}
    coreq_cache = {}
    all_combinations = list(product(*sections_by_course.values()))
    valid_combinations = []

    for comb in all_combinations:
        comb_list = list(comb)
        if not has_time_conflict(comb_list):
            try:
                extended_combinations = add_coreqs_to_combination(comb_list, cursor, coreq_cache, section_cache)
                if extended_combinations:
                    valid_combinations.extend(extended_combinations)
            except Exception as e:
                handle_coreq_error(e, str(comb))

    return valid_combinations

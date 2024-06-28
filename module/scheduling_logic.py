from itertools import product
from typing import List, Dict, Any
from . import utils
from .database_operations import retrieve_section_info
from .utils import has_time_conflict

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
    courses = df['Course_Name'].unique()  # Get unique course names from dataframe storing all selected courses, their sections, and section info
    sections_by_course = {course: df[df['Course_Name'] == course].to_dict('records') for course in courses}  # Create course-section dictionary
    coreq_cache = {}  # Create cache for coreq sections

    def get_coreqs(section: Dict[str, Any]) -> List[str]:
        """
        Get corequisite section(s) for a given section.

        Args:
            section (dict): A dictionary representing a course section.

        Returns:
            list: A list of corequisite sections.
        """
        coreqs = section.get('Coreq_Sections')  # Retrieve the coreq section(s)
        if coreqs:
            return coreqs.split(', ')  # If coreq string contains multiple coreq sections, split the string into a list at the commas
        return []

    @utils.time_function
    def add_coreqs_to_combination(combination: List[Dict[str, Any]]) -> List[List[Dict[str, Any]]]:
        """
        Add corequisite sections to a given combination of sections.

        Args:
            combination (list): A list of sections representing a combination.

        Returns:
            list: A list of extended combinations including corequisites, or an empty list if no extension is possible.
        """
        coreq_names = set(section['Name'].strip() for section in combination)  # Create a set to keep track of sections already included in a combination
        processed_coreqs = set()  # Create a set to keep track of coreq sections that have already been processed (checked for conflict and added)

        all_provisional_combinations = [combination.copy()]  # Start with the original combination

        for section in combination:  # Loop through every section in a combination
            coreqs = get_coreqs(section)  # Get coreq section(s) for the section
            new_provisional_combinations = []

            for coreq in coreqs:  # Loop through every coreq section, since a section may have multiple coreqs
                coreq = coreq.strip().upper()
                if coreq not in coreq_names and coreq not in processed_coreqs:  # If coreq section has not been included in the combination yet and has not been processed yet
                    try:
                        if coreq not in coreq_cache:  # If coreq section info is not cached yet
                            coreq_course = coreq.rsplit('-', 1)[0]  # Identify the course of the coreq section by splitting the section name at the last dash and taking the first part
                            coreq_df, _ = retrieve_section_info(cursor, [coreq_course], section_cache)  # Get section info for coreq course. Try cache first before going to the database.
                            coreq_cache[coreq] = coreq_df[coreq_df['Name'].str.strip().str.upper() == coreq].to_dict('records')  # Add retrieved section info to cache

                        coreq_section = coreq_cache[coreq]  # Otherwise, get coreq section info from cache
                        if coreq_section:  # If coreq sections exist
                            for provisional_combination in all_provisional_combinations:
                                temp_combination = provisional_combination.copy()  # Clone the original pre-coreq combination
                                temp_combination.append(coreq_section[0])  # Add the first coreq section to the basic combination of sections
                                if not has_time_conflict(provisional_combination, coreq_section[0]):  # If coreq section does not have a time conflict with any section in the basic combination
                                    new_provisional_combinations.append(temp_combination)  # Add the successful combination to new provisional combinations
                                    coreq_names.add(coreq_section[0]['Name'])  # Add coreq section to the set of sections already included in combination
                                    processed_coreqs.add(coreq)  # Add coreq section to the set of sections already processed
                    except Exception as e:
                        error_message = str(e)
                        detailed_message = f"{error_message} in section {section['Name']}"
                        if 'add_coreqs_to_combination' not in utils.errors:
                            utils.errors['add_coreqs_to_combination'] = set()
                        if detailed_message not in utils.errors['add_coreqs_to_combination']:
                            utils.errors['add_coreqs_to_combination'].add(detailed_message)
                        print(f"Error processing corequisite {coreq}: {e}")
                        continue  # Skip this coreq and continue with others

            if not new_provisional_combinations and coreqs:  # If no valid coreq was found for this section
                return []  # The combination cannot be extended
            all_provisional_combinations = new_provisional_combinations or all_provisional_combinations  # Update with new provisional combinations if any

        return all_provisional_combinations  # Return all valid combinations

    all_combinations = list(product(*sections_by_course.values()))  # Generate all possible combinations of sections using Cartesian product
    valid_combinations = []  # Initialize the list to store valid combinations
    for comb in all_combinations:  # Loop through each combination
        try:
            comb_list = list(comb)  # Convert the tuple into a list, so that it can be modified (e.g., by adding a coreq section)
            if not has_time_conflict(comb_list):  # If the sections in the basic combination do not have a time conflict
                extended_combinations = add_coreqs_to_combination(comb_list)  # Try to add coreqs to the combination
                if extended_combinations:  # If coreqs were successfully added
                    valid_combinations.extend(extended_combinations)  # Add the combination with coreqs to valid combinations
        except Exception as e:
            error_message = str(e)
            detailed_message = f"{error_message} in combination {comb}"
            if 'generate_combinations_with_coreqs' not in utils.errors:
                utils.errors['generate_combinations_with_coreqs'] = set()
            if detailed_message not in utils.errors['generate_combinations_with_coreqs']:
                utils.errors['generate_combinations_with_coreqs'].add(detailed_message)
            print(f"Error processing combination {comb}: {e}")

    return valid_combinations

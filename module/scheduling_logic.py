from itertools import product  # Import product from itertools
from . import utils  # Import the entire utils module
from .utils import has_time_conflict
from .database_operations import retrieve_section_info  # Import retrieve_section_info

@utils.time_function
def generate_combinations_with_coreqs(cursor, df, section_cache):
    courses = df['Course_Name'].unique()
    sections_by_course = {course: df[df['Course_Name'] == course].to_dict('records') for course in courses}
    coreq_cache = {}

    def get_coreqs(section):
        coreqs = section.get('Coreq_Sections')
        if coreqs:
            return coreqs.split(', ')
        return []

    @utils.time_function
    def add_coreqs_to_combination(combination):
        extended_combinations = [combination]
        coreq_names = set(section['Name'].strip() for section in combination)
        processed_coreqs = set()

        for section in combination:
            coreqs = get_coreqs(section)
            new_combinations = []
            for coreq in coreqs:
                coreq = coreq.strip().upper()
                if coreq not in coreq_names and coreq not in processed_coreqs:
                    try:
                        if coreq not in coreq_cache:
                            coreq_course = coreq.rsplit('-', 1)[0]
                            coreq_df, _ = retrieve_section_info(cursor, [coreq_course], section_cache)
                            coreq_cache[coreq] = coreq_df[coreq_df['Name'].str.strip().str.upper() == coreq].to_dict('records')

                        coreq_section = coreq_cache[coreq]
                        if coreq_section:
                            for comb in extended_combinations:
                                new_comb = comb.copy()
                                new_comb.append(coreq_section[0])
                                if not has_time_conflict(comb, coreq_section[0]):
                                    new_combinations.append(new_comb)
                            coreq_names.add(coreq_section[0]['Name'])
                            processed_coreqs.add(coreq)
                    except Exception as e:
                        error_message = str(e)
                        detailed_message = f"{error_message} in section {section['Name']}"
                        if 'add_coreqs_to_combination' not in utils.errors:
                            utils.errors['add_coreqs_to_combination'] = set()
                        if detailed_message not in utils.errors['add_coreqs_to_combination']:
                            utils.errors['add_coreqs_to_combination'].add(detailed_message)
                        print(f"Error processing corequisite {coreq}: {e}")

            if new_combinations:
                extended_combinations = new_combinations

        return extended_combinations if extended_combinations != [combination] else []

    all_combinations = list(product(*sections_by_course.values()))
    valid_combinations = []
    for comb in all_combinations:
        try:
            comb_list = list(comb)
            if not has_time_conflict(comb_list):
                extended_combinations = add_coreqs_to_combination(comb_list)
                if extended_combinations:
                    valid_combinations.extend(extended_combinations)
        except Exception as e:
            error_message = str(e)
            detailed_message = f"{error_message} in combination {comb}"
            if 'generate_combinations_with_coreqs' not in utils.errors:
                utils.errors['generate_combinations_with_coreqs'] = set()
            if detailed_message not in utils.errors['generate_combinations_with_coreqs']:
                utils.errors['generate_combinations_with_coreqs'].add(detailed_message)
            print(f"Error processing combination {comb}: {e}")

    return valid_combinations

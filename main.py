import sys
import os

# Add the current directory to sys.path for module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import time

# Updated imports to match the new directory structure
from module.database_operations import retrieve_section_info
from module.scheduling_logic import generate_combinations_with_coreqs
from module.scoring import score_combinations
from module.plotting import plot_schedules
from module.config import config
from module.utils import group_sections, print_summary, time_function, execution_times, errors

@time_function
def main():
    try:
        conn = sqlite3.connect('assets/schedule.db')
        cursor = conn.cursor()

        selected_courses = ['BIO-151', 'MAT-161', 'ENG-103', 'PSY-103']

        section_cache = {}

        df, section_columns = retrieve_section_info(cursor, selected_courses, section_cache)
        print("Section info retrieved successfully")

        grouped_df = group_sections(df)

        combinations = generate_combinations_with_coreqs(cursor, grouped_df, section_cache)

        scored_combinations = score_combinations(combinations, config)

        print_summary(scored_combinations)

        plot_schedules(scored_combinations)

    except Exception as e:
        print(f"Error in main execution: {e}")

    print("\nExecution Time Summary:")
    for func_name, times in execution_times.items():
        total_time = sum(times)
        avg_time = total_time / len(times)
        num_loops = len(times)
        print(f"{func_name}: Total time = {total_time:.4f} seconds, Average time per loop = {avg_time:.4f} seconds, Loops = {num_loops}")

    if 'main' in execution_times: # cannot figure out why @time_function does not catch main; could return to just timing the start and the end
        print(f"Total execution time: {execution_times['main'][0]:.4f} seconds")
    else:
        print("Main execution time not recorded")

    print("\nError Summary:")
    for func_name, error_set in errors.items():
        print(f"{func_name}: {len(error_set)} unique errors")
        for error_message in error_set:
            print(f"  {error_message}")

if __name__ == '__main__':
    main()

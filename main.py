import sys
import os

# Add the current directory to sys.path for module resolution
# Testing:  when this line is excluded, the script still runs fine, but that may depend on PYTHONPATH
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
import time

from module.database_operations import (retrieve_section_info, group_sections,
                                        sort_sections_by_enrollment, sort_courses_by_variance,
                                        sort_courses_by_section_count
)
from module.scheduling_logic import generate_combinations_with_coreqs
from module.scoring import score_combinations
from module.plotting import plot_schedules
from module.config import config, ACTIVATE_SORT_BY_ENROLLMENT, ACTIVATE_SORT_BY_VARIANCE
from module.utils import logger, print_summary, print_execution_summary, print_error_summary
from mockup.mockup import mock_selected_courses, mock_modality_preferences, mock_user_availability

def main():
    # Start timing (time decorator function does not seem to work with main)
    start_time = time.time()

    try:
        conn = sqlite3.connect('assets/schedule.db')
        cursor = conn.cursor()

        # Mock selected courses (get them from mockup file)
        selected_courses = mock_selected_courses()

        # Mock modality preferences
        modality_preferences = mock_modality_preferences()

        # Mock user availability
        user_availability = mock_user_availability()

        section_cache = {}

        df, section_columns = retrieve_section_info(cursor, selected_courses, section_cache)
        logger.info("Section info retrieved successfully")

        # Sort courses by section number (ascending order)
        # Theoretically, it should make a difference for time conflict checking function, but in practice it does not
        # df = sort_courses_by_section_count(df)

        # Sort courses by variance in section enrollments (within a course), if the option is activated in config
        # A light way to put a thumb on the scale in favor of sections with lower enrollment, but does not seem to make practical difference
        if ACTIVATE_SORT_BY_VARIANCE:
            df = sort_courses_by_variance(df)

        # Sort sections by enrollment (within a course), if the option is activated in config
        # A light way to put a thumb on the scale in favor of sections with lower enrollment
        if ACTIVATE_SORT_BY_ENROLLMENT:
            df = sort_sections_by_enrollment(df)

        # Group sections of the same course that meet at the same time, on the same days and dates, in the same location, and have same modality
        df = group_sections(df) # Testing:  changed argument from df to sorted_df

        # logger.info("Generating schedule combinations...")
        combinations = generate_combinations_with_coreqs(cursor, df, section_cache)
        # logger.info("Schedule combinations generated successfully")

        # logger.info("Scoring schedule combinations...")
        scored_combinations = score_combinations(combinations, user_availability, modality_preferences) # Added user_availability & modality_preferences
        # logger.info("Schedule combinations scored successfully")

        # logger.info("Printing scored schedule combinations...")
        print_summary(scored_combinations)
        # logger.info("Scored schedule combinations printed successfully")

        # logger.info("Plotting scored schedule combinations...")
        plot_schedules(scored_combinations)
        # logger.info("Scored schedule combinations plotted successfully")

    except Exception as e:
        logger.error(f"Error in main execution: {e}")

    end_time = time.time()  # End timing
    main_execution_time = end_time - start_time
    print(f"Main execution time: {main_execution_time:.4f} seconds")  # Print main execution time

    print_execution_summary()
    print_error_summary()

if __name__ == '__main__':
    main()

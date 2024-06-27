import sys
import os
import time

# Add the current directory to sys.path for module resolution
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import sqlite3
from module.database_operations import retrieve_section_info
from module.scheduling_logic import generate_combinations_with_coreqs
from module.scoring import score_combinations
from module.plotting import plot_schedules
from module.config import config
from module.utils import group_sections, print_summary, print_execution_summary, print_error_summary, time_function, logger
from mockup.mockup import mock_selected_courses, mock_modality_preferences, mock_user_availability

def main():
    start_time = time.time()  # Start timing (used to time the main) (decorator function does not seem to play nice with main)

    try:
        conn = sqlite3.connect('assets/schedule.db')
        cursor = conn.cursor()

        # Mock up selected courses (get selected courses from mockup file)
        selected_courses = mock_selected_courses()

        # Mock modality preferences and update config
        modality_preferences = mock_modality_preferences()
        config["modality_preferences"] = modality_preferences  # Update config with modality preferences

        section_cache = {}

        df, section_columns = retrieve_section_info(cursor, selected_courses, section_cache)
        logger.info("Section info retrieved successfully")

        grouped_df = group_sections(df)

        # logger.info("Generating schedule combinations...")
        combinations = generate_combinations_with_coreqs(cursor, grouped_df, section_cache)
        # logger.info("Schedule combinations generated successfully")

        # logger.info("Scoring schedule combinations...")
        scored_combinations = score_combinations(combinations)
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

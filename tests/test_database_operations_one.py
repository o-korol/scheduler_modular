import unittest
import sqlite3
# import os # Testing

# Testing adding the path
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module.database_operations import retrieve_section_info

class TestDatabaseOperations(unittest.TestCase):
    def setUp(self):
        # Use the actual test database in the assets folder
        self.test_db_path = os.path.join(os.path.dirname(__file__), '../assets/schedule.db')
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def test_retrieve_section_info(self):
        selected_courses = ['BIO-151'] # Specify the course
        section_cache = {}
        df, section_columns = retrieve_section_info(self.cursor, selected_courses, section_cache)

        # Check that the dataframe is not empty
        self.assertFalse(df.empty)
        # Check that the correct columns are present
        expected_columns = ['Course_Name', 'Name', 'Avail_Seats', 'Printed_Comments', 'Coreq_Course',
                            'Coreq_Sections', 'STime', 'ETime', 'SDate', 'EDate', 'Mtg_Days', 'Method',
                            'Credits', 'Restricted_section', 'Cohorted_section', 'Fraction_Full',
                            'Faculty_First', 'Faculty_Last', 'Faculty_Full_Name']
        self.assertEqual(section_columns, expected_columns)
        # Check that the correct number of rows are returned
        self.assertGreater(len(df), 0)  # Ensure there are rows returned

if __name__ == '__main__':
    unittest.main()

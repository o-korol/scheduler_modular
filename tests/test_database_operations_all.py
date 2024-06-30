import unittest
import sqlite3
import os
import csv
from module.database_operations import retrieve_section_info # If it has issues with this import, check test_database_operations_one for how to add path

class TestDatabaseOperations(unittest.TestCase):
    failures = []  # Declare failures as a class attribute

    def setUp(self):
        # Use the actual test database in the assets folder
        self.test_db_path = os.path.join(os.path.dirname(__file__), '../assets/schedule.db')
        self.conn = sqlite3.connect(self.test_db_path)
        self.cursor = self.conn.cursor()

    def tearDown(self):
        self.conn.close()

    def get_all_courses(self):
        # Retrieve all unique course names from the database
        self.cursor.execute("SELECT DISTINCT Course_Name FROM schedule")
        courses = self.cursor.fetchall()
        return [course[0] for course in courses]

    def test_retrieve_section_info_for_all_courses(self):
        # Get all unique courses from the database
        all_courses = self.get_all_courses()
        section_cache = {}

        for course in all_courses:
            with self.subTest(course=course):
                try:
                    df, section_columns = retrieve_section_info(self.cursor, [course], section_cache)

                    # Check that the dataframe is not empty
                    self.assertFalse(df.empty, f"Failed for course: {course}")
                    # Check that the correct columns are present
                    expected_columns = ['Course_Name', 'Name', 'Avail_Seats', 'Printed_Comments', 'Coreq_Course',
                                        'Coreq_Sections', 'STime', 'ETime', 'SDate', 'EDate', 'Mtg_Days', 'Method',
                                        'Credits', 'Restricted_section', 'Cohorted_section', 'Fraction_Full',
                                        'Faculty_First', 'Faculty_Last', 'Faculty_Full_Name']
                    self.assertEqual(section_columns, expected_columns, f"Failed for course: {course}")
                    # Check that the correct number of rows are returned
                    self.assertGreater(len(df), 0, f"Failed for course: {course}")
                except Exception as e:
                    TestDatabaseOperations.failures.append({'course': course, 'error': str(e)})

    @classmethod
    def tearDownClass(cls):
        # Write the failures to a CSV file
        if cls.failures:
            output_path = os.path.join(os.path.dirname(__file__), '../assets/database_operations_test_failures.csv')
            with open(output_path, mode='w', newline='') as file:
                writer = csv.DictWriter(file, fieldnames=['course', 'error'])
                writer.writeheader()
                for failure in cls.failures:
                    writer.writerow(failure)

if __name__ == '__main__':
    unittest.main()

import unittest
from datetime import time

# Testing adding the path
import sys
import os
# Convert this file's relative path to absolute path.  Move up one level in the directory hierarchy, twice, to reach the parent directory.  Add parent directory to Python's module search paths.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from module.scoring import _average_time

class TestAverageTime(unittest.TestCase): # Defines a test class that inherits from unittest.TestCase
    def test_average_time_case1(self): # Defines a test method
        times = [time(9, 0), time(11, 0)] # Define a list of time objects representing class start times (in this case, 9:00 am and 11:00 am)
        avg_time = _average_time(times)  # Call the function we are testing to calculate the average time
        # Assert that the calculated average time matches the expected average time (10:00 AM)
        # If the values of the frist and second argument are not equal, the test will fail, and the provided message will be displayed
        self.assertEqual(avg_time, time(10, 0), f"Expected 10:00 AM, but got {avg_time}")

    def test_average_time_case2(self):
        times = [time(8, 30), time(9, 30), time(10, 30)]
        avg_time = _average_time(times)
        self.assertEqual(avg_time, time(9, 30), f"Expected 9:30 AM, but got {avg_time}")

    def test_average_time_case3(self):
        times = [time(14, 45), time(15, 15)]
        avg_time = _average_time(times)
        self.assertEqual(avg_time, time(15, 0), f"Expected 3:00 PM, but got {avg_time}")

    def test_average_time_case4(self):
        times = [time(9, 35, 0), time(9, 35, 30)]
        avg_time = _average_time(times)
        self.assertEqual(avg_time, time(9, 35), f"Expected 9:35 AM, but got {avg_time}")

if __name__ == '__main__':
    unittest.main()

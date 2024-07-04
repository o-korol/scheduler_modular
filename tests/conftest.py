import os
import pandas as pd
import pytest
import sqlite3

@pytest.fixture(scope="module")
def db_connection():
    test_db_path = os.path.join(os.path.dirname(__file__), '../assets/schedule.db') # Establish the path to the database
    conn = sqlite3.connect(test_db_path) # Connect to database
    cursor = conn.cursor()
    yield cursor
    conn.close()

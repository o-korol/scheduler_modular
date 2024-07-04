import pytest
from module.database_operations import retrieve_section_info

@pytest.fixture
def section_cache():
    return {}

def test_retrieve_section_info(db_connection, section_cache):
    selected_courses = ['BIO-151']
    df, section_columns = retrieve_section_info(db_connection, selected_courses, section_cache)

    # Check that the dataframe is not empty
    assert not df.empty, "DataFrame should not be empty"

    # Check that the correct columns are present
    expected_columns = [
        'Course_Name', 'Name', 'Avail_Seats', 'Printed_Comments', 'Coreq_Course',
        'Coreq_Sections', 'STime', 'ETime', 'SDate', 'EDate', 'Mtg_Days', 'Method',
        'Credits', 'Restricted_section', 'Cohorted_section', 'Fraction_Full',
        'Faculty_First', 'Faculty_Last', 'Faculty_Full_Name', 'Number_Weeks', 'Location', 'Room', 'Building', 'Duration'
    ]

    assert section_columns == expected_columns, "Columns do not match expected columns"

    # Check that the correct number of rows are returned
    assert len(df) > 0, "There should be at least one row returned"

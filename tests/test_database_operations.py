import pandas as pd
import pytest

from module.database_operations import (retrieve_section_info, group_sections,
                                        sort_sections_by_enrollment, sort_courses_by_variance
)

"""Testing _retrieve_sections function. """

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
        'Faculty_First', 'Faculty_Last', 'Faculty_Full_Name', 'Number_Weeks', 'Location',
        'Room', 'Building', 'Duration', 'Fraction_Full_Deviation'
    ]

    assert section_columns == expected_columns, "Columns do not match expected columns"

    # Check that the correct number of rows are returned
    assert len(df) > 0, "There should be at least one row returned"

"""Testing _group_sections function. """


def test_not_group_sections_with_coreqs():
    """Test that sections with corequisites are not grouped."""

    # Create sample dataset that contains 3 sections of the same course: 2 with no coreqs (should be grouped) and 1 with a corequisite (should not be grouped)
    # Other than coreqs, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, 'ESL-116'],
        # One section has a corequisite and should NOT be grouped with others
        'Coreq_Sections': [None, None, 'ESL-116-101'],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "Section with corequisite should remain ungrouped"


def test_group_same_course():
    """Test grouping sections of the same course."""

    # Create sample dataset that contains 3 sections:  2 of the same course (should be grouped) and 1 of a different course (should not be grouped)
    # Other than the course names and section names, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'CHE-171'],
        # One section belongs to a different course and should not be grouped with others
        'Name': ['ENG-103-101', 'ENG-103-102', 'CHE-171-101'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, None],
        'Coreq_Sections': [None, None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'CHE-171-101' in grouped_names, "Ungrouped section should remain as is"


def test_group_same_dates():
    """Test grouping sections with the same start and end dates."""

    # Create sample dataset that contains 4 sections: 2 with the same duration (should be grouped) and 2 with a different durations (should not be grouped)
    # Other than the durations, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103', 'ENG-103-104'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-03-01 00:00:00', '2024-04-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, None, None],
        'Coreq_Sections': [None, None, None, None],
        # Different durations
        'Duration': ['Full Semester', 'Full Semester', '1st Half', '2nd Half'],
        'Method': ['LEC', 'LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 3, "Grouped DataFrame should have three rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "1st Half section should remain ungrouped"
    assert 'ENG-103-104' in grouped_names, "2nd Half section should remain ungrouped"


def test_group_same_times():
    """Test grouping sections with the same start and end times."""

    # Create sample dataset that contains 3 sections: 2 with the same times (should be grouped) and 1 with a different time (should not be grouped)
    # Other than the times, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103'],
        'STime': ['08:00 AM', '08:00 AM', '09:00 AM'],  # Different times
        'ETime': ['09:00 AM', '09:00 AM', '10:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, None],
        'Coreq_Sections': [None, None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "Section with different time should remain ungrouped"


def test_group_same_days():
    """Test grouping sections with the same meeting days."""

    # Create sample dataset that contains 3 sections: 2 with the same meeting days (should be grouped), and 1 with different meeting days (should not be grouped)
    # Other than the meeting days, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'T, TH'],  # Different meeting days
        'Coreq_Course': [None, None, None],
        'Coreq_Sections': [None, None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "Section with different meeting days should remain ungrouped"


def test_group_same_modality():
    """Test grouping sections with the same modality."""

    # Create sample dataset that contains 3 sections: 2 with the same modality (should be grouped), and 1 with different modality (should not be grouped)
    # Other than the modality, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, None],
        'Coreq_Sections': [None, None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'HYB'],  # Different modalities
        'Location': ['MC', 'MC', 'MC']
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "Section with different location should remain ungrouped"


def test_group_same_location():
    """Test grouping sections with the same location."""

    # Create sample dataset that contains 3 sections: 2 with the same location (should be grouped), and 1 with different location (should not be grouped)
    # Other than location, all sections have the same attributes
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103'],
        'STime': ['08:00 AM', '08:00 AM', '08:00 AM'],
        'ETime': ['09:00 AM', '09:00 AM', '09:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F'],
        'Coreq_Course': [None, None, None],
        'Coreq_Sections': [None, None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester'],
        'Method': ['LEC', 'LEC', 'LEC'],
        'Location': ['MC', 'MC', 'NC']  # Different locations
    }
    df = pd.DataFrame(data)

    # Group sections
    grouped_df = group_sections(df)

    # Check the number of rows after grouping
    assert len(grouped_df) == 2, "Grouped DataFrame should have two rows"

    # Verify the content of the grouped DataFrame
    grouped_names = grouped_df['Name'].values
    assert 'ENG-103-101, ENG-103-102' in grouped_names, "Grouped sections should be combined"
    assert 'ENG-103-103' in grouped_names, "Section with different location should remain ungrouped"


"""Testing sort_sections_by_enrollment function"""
def test_sort_sections_by_enrollment():
    """Test sorting of sections first by Course_Name and then by Fraction_Full, in ascending order."""

    # Create a sample dataset with sections from different courses and varying Fraction_Full values
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103', 'MAT-143', 'MAT-143'], # 2 different courses
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103', 'MAT-143-104', 'MAT-143-105'],
        'Fraction_Full': [0.25, 0.3, 0.5, 0.5, 0.9] # Different sections have different enrollment
    }
    df = pd.DataFrame(data)

    # Apply the sorting function
    sorted_df = sort_sections_by_enrollment(df)

    # Expected sorted order
    expected_order = ['ENG-103-101', 'ENG-103-102', 'ENG-103-103', 'MAT-143-104', 'MAT-143-105']

    # Verify the sorting order
    sorted_names = sorted_df['Name'].values
    assert list(sorted_names) == expected_order, "Sections should be sorted by Course_Name Fraction_Full in ascending order"

    # Additional checks for sorting correctness
    assert sorted_df.iloc[0]['Fraction_Full'] == 0.25, "ENG-103-101 should have Fraction_Full of 0.25"
    assert sorted_df.iloc[1]['Fraction_Full'] == 0.3, "ENG-103-102 should have Fraction_Full of 0.3"
    assert sorted_df.iloc[2]['Fraction_Full'] == 0.5, "ENG-103-103 should have Fraction_Full of 0.5"
    assert sorted_df.iloc[3]['Fraction_Full'] == 0.5, "MAT-143-104 should have Fraction_Full of 0.5"
    assert sorted_df.iloc[4]['Fraction_Full'] == 0.9, "MAT-143-105 should have Fraction_Full of 0.9"


"""Testing sort_courses_by_variance function"""
def test_sort_courses_by_variance():
    """Test sorting of courses by the variance of their section enrollments in descending order."""

    # Create a sample dataset with sections from different courses and varying Fraction_Full values
    data = {
        'Course_Name': ['ENG-103', 'ENG-103', 'ENG-103', 'MAT-143', 'MAT-143', 'PHY-201', 'PHY-201'],
        'Name': ['ENG-103-101', 'ENG-103-102', 'ENG-103-103', 'MAT-143-104', 'MAT-143-105', 'PHY-201-101', 'PHY-201-102'],
        'Fraction_Full': [0.25, 0.5, 0.75, 0.2, 0.7, 0.8, 0.9] # Different variances, calculated form Fraction_Full
    }
    df = pd.DataFrame(data)

    # Apply the sorting function
    sorted_df = sort_courses_by_variance(df)

    # Expected sorted order based on variance
    # MAT-143 has the highest variance (0.125), ENG-103 has 0.0625, and PHY-201 has the lowest variance (0.005)
    # Fraction_Full for ENG-103 sections: [0.25, 0.5, 0.75]
    # Mean: (0.25 + 0.5 + 0.75) / 3 = 0.5
    # Variance: ((0.25 - 0.5)² + (0.5 - 0.5)² + (0.75 - 0.5)²) / 2 = 0.0625
    expected_order = ['MAT-143', 'ENG-103', 'PHY-201']

    # Verify the sorting order
    sorted_course_names = sorted_df['Course_Name'].unique()
    assert list(sorted_course_names) == expected_order, "Courses should be sorted by variance of Fraction_Full in descending order"

    # Additional checks for variance correctness
    # Group sections by Course_Name, calculate the variance of Fraction_Full for each group, and select the variance for MAT-143 group.
    # Check if it is approximately 0.125 within a tolerance of 0.001.
    assert sorted_df.groupby('Course_Name')['Fraction_Full'].var().loc['MAT-143'] == pytest.approx(0.125, 0.001), "MAT-143 should have a variance of approximately 0.125"
    assert sorted_df.groupby('Course_Name')['Fraction_Full'].var().loc['ENG-103'] == pytest.approx(0.0625, 0.001), "ENG-103 should have a variance of approximately 0.0625"
    assert sorted_df.groupby('Course_Name')['Fraction_Full'].var().loc['PHY-201'] == pytest.approx(0.005, 0.001), "PHY-201 should have a variance of approximately 0.005"

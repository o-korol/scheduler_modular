import pytest
import pandas as pd
from datetime import datetime, time
from module.utils import (
    group_sections, parse_time, parse_date, parse_time_range,
    time_difference_in_minutes, has_time_conflict, sort_combination,
    print_summary, execution_times, errors, time_function
)

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


"""Testing _parse_time function."""


def test_parse_time():
    """Test the parse_time function."""
    assert parse_time('08:00 AM') == time(8, 0), "Parsed time should be 08:00 AM"
    assert parse_time('11:59 PM') == time(23, 59), "Parsed time should be 11:59 PM"
    assert parse_time('') is None, "Empty string should return None"


"""Testing _parse_date function."""


def test_parse_date():
    """Test the parse_date function."""
    assert parse_date('2024-01-01 08:00:00') == datetime(2024, 1, 1, 8,
                                                         0, 0), "Parsed date should be 2024-01-01 08:00:00"
    assert parse_date('') is None, "Empty string should return None"


"""Testing _parse_time_range function."""


def test_parse_time_range():
    """Test the parse_time_range function."""
    start, end = parse_time_range('08:00 AM - 09:00 AM')
    assert start == time(8, 0), "Start time should be 08:00 AM"
    assert end == time(9, 0), "End time should be 09:00 AM"


"""Testing _time_difference_in_minutes function."""


def test_time_difference_in_minutes():
    """Test the time_difference_in_minutes function."""
    t1 = time(9, 0)
    t2 = time(8, 0)
    assert time_difference_in_minutes(t1, t2) == 60, "Difference should be 60 minutes"


"""Testing _has_time_conflict function."""


def test_has_time_conflict():
    """Test the has_time_conflict function."""

    # Create sample dataset that contains sections that do NOT have time conflict with each other
    # Other than the meeting times, all sections have the same non-name attributes
    data = {
        'Course_Name': ['ENG-103', 'BIO-151', 'CHE-171'],
        'Name': ['ENG-103-101', 'BIO-151-102', 'CHE-171-101'],
        'STime': ['08:00 AM', '09:00 AM', '10:00 AM'],  # Different meeting times
        'ETime': ['09:00 AM', '10:00 AM', '11:00 AM'],
        'SDate': ['2024-01-01 00:00:00', '2024-01-01 00:00:00', '2024-01-01 00:00:00'],
        'EDate': ['2024-05-01 00:00:00', '2024-05-01 00:00:00', '2024-05-01 00:00:00'],
        'Mtg_Days': ['M, W, F', 'M, W, F', 'M, W, F']
    }
    df = pd.DataFrame(data)

    # Convert the DataFrame to a list of dictionaries
    sections = df.to_dict('records')

    # Check for time conflicts
    assert has_time_conflict(
        sections) is False, "There should be no conflict among the sample sections"


"""Testing _sort_combination function."""


def test_sort_combination():
    """Test the sort_combination function."""

    # Create sample data to sort sections for printed output:  sort by the meeting time of the section's first meeting
    # Sections without meeting times or days (e.g., ONLIN, INTRN, etc) should be listed last, sorted alphabetically by course name
    data = {
        'Course_Name': ['ENG-103', 'BIO-151', 'CHE-171', 'PSY-103', 'BMC-190'],
        'Name': ['ENG-103-101', 'BIO-151-101', 'CHE-171-101', 'PSY-103-101', 'BMC-190-101'],
        'STime': ['08:00 AM', '09:00 AM', '10:00 AM', None, None],
        'ETime': ['09:00 AM', '10:00 AM', '11:00 AM', None, None],
        'Mtg_Days': ['M, W, F', 'T, TH', 'M, W', None, None],
        'Duration': ['Full Semester', 'Full Semester', 'Full Semester', 'Full Semester', 'Full Semester'],
        # Two sections have no meeting times or dates (should be listed last)
        'Method': ['LEC', 'LEC', 'LEC', 'ONLIN', 'INTRN']
    }
    df = pd.DataFrame(data)

    # Convert the DataFrame to a list of dictionaries
    combination = df.to_dict('records')

    # Sort the combination
    sorted_combination = sort_combination(combination)
    first_section = sorted_combination[0]

    # Check that the first section is correctly sorted
    assert first_section['Course_Name'] == 'ENG-103', "First sorted section should be ENG-103"
    assert first_section['STime'] == '08:00 AM', "First sorted section should start at 08:00 AM"
    assert first_section['Mtg_Days'][0] == 'M', "First sorted section should meet on Monday"

    # Check the sorting order for the rest of the sections
    sorted_course_names = [section['Course_Name'] for section in sorted_combination]
    # The expected order based on the current sorting logic of the sort_combination function
    expected_order = ['ENG-103', 'CHE-171', 'BIO-151', 'BMC-190', 'PSY-103']
    assert sorted_course_names == expected_order, f"Courses should be sorted in the correct order: {expected_order}"


def test_print_summary(capsys):
    """Test the print_summary function with captured output."""

    # Create sample data:  a list of tuples, each of which contains two items, a list of sections in a particular combination and the desirability score for that combination
    # The function receives scored_combination, which are already sorted by combined_score, with the lowest (best) scores first
    scored_combinations = [
        (
            [
                {'Name': 'BIO-151-101', 'Mtg_Days': 'M, W, F',
                    'STime': '08:00 AM', 'ETime': '09:00 AM', 'Method': 'LEC'},
                {'Name': 'CHE-171-102', 'Mtg_Days': 'M, W, F',
                    'STime': '08:00 AM', 'ETime': '09:00 AM', 'Method': 'LEC'}
            ],
            {'score': 1}
        ),
        (
            [
                {'Name': 'CHE-171-101', 'Mtg_Days': 'T, TH',
                    'STime': '10:00 AM', 'ETime': '11:00 AM', 'Method': 'LEC'},
                {'Name': 'CHE-151-102', 'Mtg_Days': 'T, TH',
                    'STime': '10:00 AM', 'ETime': '11:00 AM', 'Method': 'LEC'}
            ],
            {'score': 2}
        )
    ]

    # Call the function that prints to the console
    print_summary(scored_combinations)

    # Capture the output
    captured = capsys.readouterr()

    # Assert that the expected output is in the captured output
    assert "Generated valid schedule combinations" in captured.out, "Output should contain summary message"
    assert "Option 1: Score = 1" in captured.out, "Output should contain details of the first combination"
    assert "BIO-151-101 (M, W, F 08:00 AM - 09:00 AM)" in captured.out, "Output should contain details of the first section in the first combination"
    assert "Option 2: Score = 2" in captured.out, "Output should contain details of the second combination"
    assert "CHE-171-101 (T, TH 10:00 AM - 11:00 AM)" in captured.out, "Output should contain details of the first section in the second combination"

import pandas as pd
from typing import List, Dict, Any, Tuple

from module import utils


@utils.time_function
def retrieve_section_info(cursor: Any,
                          selected_courses: List[str],
                          section_cache: Dict[str, List[Any]]
) -> Tuple[pd.DataFrame, List[str]]:

    """
    Retrieve section data from the database for the given selected courses.

    Args:
        cursor (sqlite3.Cursor): The database cursor to execute SQL queries.
        selected_courses (list): A list of selected course names to retrieve sections for.
        section_cache (dict): A cache dictionary to store previously retrieved sections.

    Returns:
        tuple: A DataFrame containing the retrieved sections and a list of section column names.
    """
    data = []

    for course in selected_courses:
        try:
            if course in section_cache:
                data.extend(section_cache[course])
            else:
                print(f"\nProcessing course: {course}")
                cursor.execute("""
                    SELECT Course_Name, Name, Avail_Seats, Printed_Comments, Coreq_Course, Coreq_Sections,
                            STime, ETime, SDate, EDate, Mtg_Days, Method, Credits, Restricted_section, Cohorted_section,
                            Fraction_Full, Faculty_First, Faculty_Last, Faculty_Full_Name, Number_Weeks,
                            Location, Room, Building, Duration, Fraction_Full_Deviation
                    FROM schedule
                    WHERE Course_Name = ? AND Status = 'A' AND Avail_Seats > 0
                """, (course,))
                sections = cursor.fetchall()
                print(f"Retrieved sections for {course}: {sections}")

                section_cache[course] = sections  # Cache the retrieved sections
                data.extend(sections)
        except Exception as e:
            utils.errors['retrieve_section_info'].add(f"{str(e)} in course {course}")

    if data:
        section_columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(data, columns=section_columns)
    else:
        section_columns = []
        df = pd.DataFrame()

    return df, section_columns


@utils.time_function
def group_sections(df: pd.DataFrame) -> pd.DataFrame:
    """
    Group sections of the same course if they meet at the same time, on the same days and dates,
    in the same location, and have the same modality.

    Args:
        df (pd.DataFrame): The DataFrame containing section data to be grouped.

    Returns:
        pd.DataFrame: A DataFrame with grouped sections.
    """
    groups = {}  # Initialize a dictionary for the groups of sections
    # Create two separate dataframes, one containing sections with coreqs and one, without
    coreq_df = df[pd.notna(df['Coreq_Sections'])]
    non_coreq_df = df[pd.isna(df['Coreq_Sections'])]

    # Group sections of the same course
    # This grouping is applied ONLY to courses that do NOT have corequisites
    for _, row in non_coreq_df.iterrows():  # Iterate over the rows of the dataframe
        # Create a tuple key consisting of values of the current row, to uniquely identify a group
        key = (row['Course_Name'], row['STime'], row['ETime'], row['Mtg_Days'],
               row['Duration'], row['Method'], row['Location'])
        if key not in groups:  # If this key tuple has not been seen yet
            groups[key] = []  # Initialize a list for a new group
        groups[key].append(row['Name'])  # Add the section name to the group

    grouped_df = []
    for group, names in groups.items():
        group_name = ', '.join(names)  # Combine section names into a single string
        # Get a representative row from the group
        example_row = non_coreq_df[non_coreq_df['Name'] == names[0]].iloc[0].copy()
        example_row['Name'] = group_name  # Update the 'Name' field with the combined group name
        grouped_df.append(example_row)  # Add the updated row to the grouped dataframe

    grouped_df = pd.DataFrame(grouped_df)  # Convert the list of grouped rows to a dataframe

    # Concatenate grouped dataframe and corequisite dataframe
    final_df = pd.concat([grouped_df, coreq_df], ignore_index=True)
    return final_df


@utils.time_function
def sort_sections_by_enrollment(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort sections by Course_Name first, then by Fraction_Full in ascending order.
    Used to prioritize sections with lower enrollment for section load balancing.

    Args:
        df (pd.DataFrame): The DataFrame containing section data to be sorted.

    Returns:
        pd.DataFrame: The sorted DataFrame.
    """
    sorted_df = df.sort_values(by=['Course_Name', 'Fraction_Full'], ascending=[True, True])
    return sorted_df


@utils.time_function
def sort_courses_by_variance(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort courses by the variance of their section enrollments.
    Originally planned to use it for enrollment balancing, but took a different path.

    Args:
        df (pd.DataFrame): The DataFrame containing section data to be sorted by variance.

    Returns:
        pd.DataFrame: The sorted DataFrame.
    """
    # Group by 'Course_Name' and calculate the variance of 'Fraction_Full' for each group
    variance_df = df.groupby('Course_Name')['Fraction_Full'].var().reset_index()
    variance_df.columns = ['Course_Name', 'Variance']

    # Merge the variance back into the original dataframe
    df = pd.merge(df, variance_df, on='Course_Name')

    # Sort the dataframe first by the variance in descending order, then by 'Course_Name' and 'Fraction_Full'
    # Consider whether I want to sort by Fraction_Full here or in sort_sections_by_enrollment function
    sorted_df = df.sort_values(
        by=['Variance', 'Course_Name', 'Fraction_Full'], ascending=[False, True, True])

    # Drop the 'Variance' column as it is no longer needed
    sorted_df = sorted_df.drop(columns=['Variance'])

    return sorted_df


@utils.time_function
def sort_courses_by_section_count(df: pd.DataFrame) -> pd.DataFrame:
    """
    Sort courses by the number of sections they have in ascending order.
    Considered using for optimizing time conflict check, but it did not make practical difference.

    Args:
        df (pd.DataFrame): The DataFrame containing section data to be sorted by section count.

    Returns:
        pd.DataFrame: The sorted DataFrame.
    """
    # Count the number of sections for each course
    section_count_df = df.groupby('Course_Name').size().reset_index(name='Section_Count')

    # Print the section count dataframe
    print("Section Count DataFrame:")
    print(section_count_df)

    # Merge the section count back into the original dataframe
    df = pd.merge(df, section_count_df, on='Course_Name')

    # Print the DataFrame before sorting
    print("DataFrame before sorting by section count:")
    print(df)

    # Sort the dataframe first by the number of sections in ascending order, then by 'Course_Name'
    sorted_df = df.sort_values(by=['Section_Count', 'Course_Name'], ascending=[True, True])

    # Print the DataFrame after sorting
    print("DataFrame after sorting by section count:")
    print(sorted_df)

    # Drop the 'Section_Count' column as it is no longer needed
    sorted_df = sorted_df.drop(columns=['Section_Count'])

    return sorted_df

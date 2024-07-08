import logging
import pandas as pd
import re
import sqlite3
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


def read_csv(file_name):
    try:
        df = pd.read_csv(file_name)
        logging.info(f'Successfully read {file_name}')
        return df
    except Exception as e:
        logging.error(f'Error reading {file_name}: {e}')
        sys.exit(1)


def clean_column_names(df):
    df.columns = df.columns.str.strip().str.replace(' ', '_').str.replace(r'[^\w]', '_', regex=True)
    df = df.rename(columns={'__Weeks': 'Number_Weeks'})
    logging.info('Column names cleaned and renamed')
    return df


def adjust_data_types(df):
    # 'Name' is the section identifier (e.g., ENG-103-101), not the course identifier (e.g., ENG-103)
    # Course identifier is 'Course_Name'
    string_columns = [
        'Sub', 'Term', 'Dept', 'Name', 'Short_Title', 'Status', 'Mtg_Days', 'STime', 'ETime',
        'Faculty_First', 'Faculty_Last', 'Petition_Y_N', 'Printed_Comments', 'Method', 'Type',
        'Location', 'Room', 'Sec_Course_Types'
    ]
    for col in string_columns:
        df[col] = df[col].astype(str).str.strip()

    # Additional cleanup for the 'Room' column.
    # Without it, Room column retains 'nan', which can interfere with building information extraction.
    df['Room'] = df['Room'].replace('nan', None)
    df['Room'] = df['Room'].replace('', None)

    datetime_columns = ['Date_Run', 'Status_Date', 'SDate', 'EDate']
    for col in datetime_columns:
        df[col] = pd.to_datetime(df[col])

    logging.info('Data types adjusted')
    return df


def handle_multiple_entries(df):
    '''Some sections have multiple times, e.g., 9:35 AM, 9:35 AM, in order to reserve multiple rooms.
     This function peels off anything beyond the first entry and saves it in the Time_Extra column.
     This does not appear critical for scheduling and may be disposed of in the future.'''
    df['STime_Extra'] = df['STime']
    df['ETime_Extra'] = df['ETime']
    df['STime'] = df['STime'].str.split(',', n=1).str[0].str.strip()
    df['ETime'] = df['ETime'].str.split(',', n=1).str[0].str.strip()
    logging.info('Handled multiple entries in STime and ETime')
    return df


def extract_course_name(name):
    '''Extract course identifier (e.g., ENG-103) from section identifier (e.g., ENG-103-101)'''
    parts = name.split('-')  # Could have used rsplit
    if len(parts) >= 2:
        return '-'.join(parts[:2])
    return name


def extract_corequisites(comments):
    '''The info about co-reqs is contained in the Printed Comments column &
    always follows the same format ("C/co-requisite:  X, Y, Z.")'''
    if pd.isna(comments):
        return None, None  # Updated to return a tuple
    coreq_match = re.search(r'Co-requisite:\s*([\w\d\s,or-]+)', comments, re.IGNORECASE)
    if not coreq_match:
        return None, None  # Updated to return a tuple
    coreq_text = coreq_match.group(1).strip()
    coreqs = []
    coreq_courses = set()  # Use a set to collect unique course names
    parts = re.split(r'\s*,\s*|\s+or\s+', coreq_text)
    for part in parts:
        if '-' in part:
            coreqs.append(part)
            course_name = extract_course_name(part)  # Extract course name
            coreq_courses.add(course_name)  # Add to the set of course names
        elif coreqs:
            last_coreq = coreqs[-1]
            new_coreq = last_coreq[:-3] + part[-3:]
            coreqs.append(new_coreq)
            course_name = extract_course_name(new_coreq)  # Extract course name
            coreq_courses.add(course_name)  # Add to the set of course names
    # Return both courses and sections
    return ', '.join(coreq_courses) if coreq_courses else None, ', '.join(coreqs) if coreqs else None


def extract_only_sentence(comments):
    ''' Identify sections restricted to specific populations
    (PTECH students, students in specific online programs, etc) '''
    if pd.isna(comments):
        return None
    sentences = re.findall(r'([^.!?]*\bonly\b[^.!?]*[.!?])', comments, re.IGNORECASE)
    if sentences:
        sentence = sentences[0].strip()
        cleaned_sentence = re.sub(r'^[,.\s]+', '', sentence)  # Remove leading punctuation or spaces
        return cleaned_sentence if cleaned_sentence else None  # Ensure empty strings are converted to None
    return None


def extract_meets_with_sections(comments):
    '''Some sections are cross-listed with different departments'''
    if pd.isna(comments):
        return None
    meets_with_match = re.search(r'meets with\s*([\w\d\s,-]+)(?=\.)', comments, re.IGNORECASE)
    if not meets_with_match:
        return None
    meets_with_text = meets_with_match.group(1).strip()
    sections = re.split(r'\s*,\s*|\s+and\s+', meets_with_text)
    # Ensure empty strings are converted to None
    return ', '.join(section.strip() for section in sections) if sections else None


def extract_building_info(df):
    '''Extract the building identifier from Room info '''
    def extract_building_from_room(room):
        if pd.isna(room) or room is None or len(room.strip()) == 0:
            return None
        parts = room.strip().split(' ')
        if parts:
            building = parts[0]
            if len(building) > 0:
                return building[0]
        return None

    df['Building'] = df['Room'].apply(extract_building_from_room)
    logging.info('Extracted building information from Room column')
    return df


def classify_duration(df):
    '''Classify section duration as full semester, 1st half, 2nd half, or partial
    based on their start and end dates'''
    # Identify semester dates
    semester_start = df['SDate'].min()
    semester_end = df['EDate'].max()
    midpoint = semester_start + (semester_end - semester_start) / 2
    first_half_end = midpoint - pd.Timedelta(days=1)  # 1st half ends 1 day before the midpoint
    second_half_start = midpoint + pd.Timedelta(days=1)  # 2nd half starts 1 day after the midpoint

    def classify_section(row):
        start_date = row['SDate']  # Get section start date
        end_date = row['EDate']  # Get section end date

        if start_date == semester_start and end_date == semester_end:  # Compare section's start and end dates to semester's dates
            return 'full semester'
        elif abs(end_date - first_half_end).days <= 1:
            return '1st half'
        elif abs(start_date - second_half_start).days <= 1:
            return '2nd half'
        else:
            return 'partial'

    df['Duration'] = df.apply(classify_section, axis=1)
    logging.info('Classified sections based on start and end dates')
    return df


def identify_cohorted_sections(df):
    df['Cohorted_section'] = df['Short_Title'].str.startswith('CH: ').astype(bool)
    logging.info('Identified cohorted sections')
    return df


def process_comments(df):
    df['Course_Name'] = df['Name'].apply(extract_course_name)
    df[['Coreq_Course', 'Coreq_Sections']] = df['Printed_Comments'].apply(
        lambda x: pd.Series(extract_corequisites(x)))
    df['Meets_With'] = df['Printed_Comments'].apply(extract_meets_with_sections)
    df['Restricted_section'] = df['Printed_Comments'].apply(extract_only_sentence)
    df = identify_cohorted_sections(df)

    logging.info('Extracted information from comments')
    return df


def calculate_fraction_full(df):
    '''Calculate how full a section is'''
    # Could have used Students instead of the difference between capacity and available seats
    df['Fraction_Full'] = ((df['Cap'] - df['Avail_Seats']) / df['Cap'])
    logging.info('Calculated Fraction_Full')
    return df


def calculate_fraction_full_deviation(df):
    '''Calculate how much a section's fill rate deviates from the typical fill rate
    for the open sections of course.  The deviation is calculated as difference from median.'''
    # Initialize Fraction_Full_Deviation column with None
    df['Fraction_Full_Deviation'] = None

    # Filter the dataframe to include only active sections with available seats
    active_df = df[(df['Status'] == 'A') & (df['Avail_Seats'] > 0)]

    # Calculate the median of Fraction_Full for each course
    course_stats = active_df.groupby('Course_Name')['Fraction_Full'].agg(['median']).reset_index()
    course_stats = course_stats.rename(columns={'median': 'Median_Fraction_Full'})

    # Merge median back into the filtered dataframe
    active_df = active_df.merge(course_stats, on='Course_Name', how='left')

    # Calculate the deviation from the median for the filtered dataframe
    active_df['Fraction_Full_Deviation'] = active_df['Fraction_Full'] - \
        active_df['Median_Fraction_Full']

    # Ensure Fraction_Full_Deviation is of type float
    active_df['Fraction_Full_Deviation'] = active_df['Fraction_Full_Deviation'].astype(float)

    # Merge the calculated deviations back into the original dataframe based on 'Name'
    df = df.drop(columns=['Fraction_Full_Deviation']).merge(
        active_df[['Name', 'Fraction_Full_Deviation']], on='Name', how='left')

    logging.info('Calculated Fraction_Full_Deviation using median deviation')

    return df


def standardize_missing_values(df):
    df.replace({'nan': None, ' ': None}, inplace=True)
    df.replace({pd.NaT: None}, inplace=True)
    logging.info('Standardized missing values')
    return df


def combine_instructor_names(df):
    df['Faculty_Full_Name'] = df['Faculty_First'].fillna('') + ' ' + df['Faculty_Last'].fillna('')
    df['Faculty_Full_Name'] = df['Faculty_Full_Name'].str.strip()  # Remove any leading/trailing spaces
    logging.info('Combined instructor names into Faculty_Full_Name')
    return df


def save_to_csv(df, file_name):
    cleaned_file_name = 'cleaned_' + file_name
    df.to_csv(cleaned_file_name, index=False)
    logging.info(f'Cleaned data saved to {cleaned_file_name}')


def import_to_sqlite(df, db_name):
    try:
        conn = sqlite3.connect(db_name)
        df.to_sql('schedule', conn, if_exists='replace', index=False)
        cursor = conn.cursor()

        # Adding indexes
        # May need to add more indexes later when it is clear what the db is searched for
        cursor.execute("CREATE INDEX idx_course_name ON schedule (Course_Name)")
        cursor.execute("CREATE INDEX idx_name ON schedule (Name)")
        cursor.execute("CREATE INDEX idx_status ON schedule (Status)")
        cursor.execute("CREATE INDEX idx_avail_seats ON schedule (Avail_Seats)")
        cursor.execute("CREATE INDEX idx_faculty_last ON schedule (Faculty_Last)")

        cursor.execute("PRAGMA table_info(schedule)")
        columns_info = cursor.fetchall()
        for column in columns_info:
            print(column)
        conn.close()
        logging.info(f'Data imported into SQLite database {db_name}')
    except Exception as e:
        logging.error(f'Error importing data to SQLite: {e}')
        sys.exit(1)


def main():
    logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG for detailed output
    file_name = 'sample_schedule_SP24_6.csv'  # Specify the name of the .csv master schedule file
    db_name = 'schedule.db'  # Specify the name of the database

    df = read_csv(file_name)
    df = clean_column_names(df)
    df = adjust_data_types(df)
    df = handle_multiple_entries(df)
    df = extract_building_info(df)  # Extract building name from room information
    df = classify_duration(df)  # Classify sections as full-semester, 1st half, 2nd half, or partial
    df = process_comments(df)
    df = calculate_fraction_full(df)  # Calculate how full each section is
    df = calculate_fraction_full_deviation(df)  # Calculate deviation from the course median
    df = standardize_missing_values(df)  # First, standardize missing values
    # Alternatively, clean up names columns to convert 'nan' to None, as was done with Room
    # Second, combine faculty first and last names (otherwise, NaN is not handled correctly)
    df = combine_instructor_names(df)

    # Convert any remaining empty strings to None (this is insurance)
    df.replace('', None, inplace=True)

    save_to_csv(df, file_name)
    import_to_sqlite(df, db_name)
    logging.info('Script completed successfully')


if __name__ == "__main__":
    main()

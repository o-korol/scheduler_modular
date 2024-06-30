# Cleans up .csv data and load it into database
# This version is modular & inlcudes improved logging, error handling, and configuration management
import pandas as pd
import re
import sqlite3
import logging
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

    # Additional cleanup for the 'Room' column.  Without it, Room column retains 'nan', which can interfere with building information extraction.
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
    parts = name.split('-') # Could have used rsplit
    if len(parts) >= 2:
        return '-'.join(parts[:2])
    return name

def extract_corequisites(comments):
    '''The info about co-reqs is contained in the Printed Comments column & always follows the same format ("C/co-requisite:  X, Y, Z."). '''
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
    return ', '.join(coreq_courses) if coreq_courses else None, ', '.join(coreqs) if coreqs else None  # Return both courses and sections

def extract_only_sentence(comments):
    ''' Identify sections restricted to specific populations (PTECH students, students in specific online programs, etc) '''
    if pd.isna(comments):
        return None
    sentences = re.findall(r'([^.!?]*\bonly\b[^.!?]*[.!?])', comments, re.IGNORECASE)
    if sentences:
        sentence = sentences[0].strip()
        cleaned_sentence = re.sub(r'^[,.\s]+', '', sentence)  # Remove leading punctuation or spaces
        return cleaned_sentence if cleaned_sentence else None  # Ensure empty strings are converted to None
    return None

def extract_meets_with_sections(comments):
    '''Some sections are cross-listed with different departments '''
    if pd.isna(comments):
        return None
    meets_with_match = re.search(r'meets with\s*([\w\d\s,-]+)(?=\.)', comments, re.IGNORECASE)
    if not meets_with_match:
        return None
    meets_with_text = meets_with_match.group(1).strip()
    sections = re.split(r'\s*,\s*|\s+and\s+', meets_with_text)
    return ', '.join(section.strip() for section in sections) if sections else None  # Ensure empty strings are converted to None

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

def identify_cohorted_sections(df):
    df['Cohorted_section'] = df['Short_Title'].str.startswith('CH: ').astype(bool)
    logging.info('Identified cohorted sections')
    return df

def process_comments(df):
    df['Course_Name'] = df['Name'].apply(extract_course_name)
    df[['Coreq_Course', 'Coreq_Sections']] = df['Printed_Comments'].apply(lambda x: pd.Series(extract_corequisites(x)))
    df['Meets_With'] = df['Printed_Comments'].apply(extract_meets_with_sections)
    df['Restricted_section'] = df['Printed_Comments'].apply(extract_only_sentence)
    df = identify_cohorted_sections(df)

    logging.info('Extracted information from comments')
    return df

def calculate_fraction_full(df):
    df['Fraction_Full'] = ((df['Cap'] - df['Avail_Seats']) / df['Cap']) # Could have used Students instead of the difference between capacity and available seats
    logging.info('Calculated Fraction_Full')
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
        cursor.execute("CREATE INDEX idx_course_name ON schedule (Course_Name)")
        cursor.execute("CREATE INDEX idx_name ON schedule (Name)")
        cursor.execute("CREATE INDEX idx_status ON schedule (Status)")
        cursor.execute("CREATE INDEX idx_avail_seats ON schedule (Avail_Seats)")
        cursor.execute("CREATE INDEX idx_faculty_last ON schedule (Faculty_Last)") # May need to adjust this later to Full_Name

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
    logging.basicConfig(level=logging.DEBUG)  # Set logging level to DEBUG for detailed output # Testing
    file_name = 'sample_schedule_SP24_6.csv' # Specify the name of the .csv master schedule file
    db_name = 'schedule.db'

    df = read_csv(file_name)
    df = clean_column_names(df)
    df = adjust_data_types(df)
    df = handle_multiple_entries(df)
    df = extract_building_info(df)
    df = process_comments(df)
    df = calculate_fraction_full(df)
    df = standardize_missing_values(df) # First, standardize missing values
    df = combine_instructor_names(df) # Second, combine faculty first and last names (otherwise, NaN is not handled correctly)

    # Convert any remaining empty strings to None (this is insurance)
    df.replace('', None, inplace=True)

    save_to_csv(df, file_name)
    import_to_sqlite(df, db_name)
    logging.info('Script completed successfully')

if __name__ == "__main__":
    main()

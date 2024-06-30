import pandas as pd
from . import utils  # Import the entire utils module

@utils.time_function
def retrieve_section_info(cursor, selected_courses, section_cache):
    data = []

    for course in selected_courses:
        try:
            if course in section_cache:
                data.extend(section_cache[course])
            else:
                print(f"\nProcessing course: {course}")
                cursor.execute("""
                    SELECT Course_Name, Name, Avail_Seats, Printed_Comments, Coreq_Course, Coreq_Sections, STime, ETime, SDate, EDate, Mtg_Days, Method, Credits, Restricted_section, Cohorted_section, Fraction_Full, Faculty_First, Faculty_Last, Faculty_Full_Name, Number_Weeks, Location, Room, Building
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

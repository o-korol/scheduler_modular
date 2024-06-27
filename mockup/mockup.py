# Mock up of user input:  course selection, modality preference, and availability

# Tested out successfully
def mock_selected_courses():
    """
    Mock function to simulate user-selected courses.
    """
    selected_courses = ['BIO-151', 'MAT-161', 'ENG-103', 'PSY-103']
    return selected_courses

# Testing
def mock_modality_preferences():
    """
    Mock function to simulate user input for modality preferences.
    Make sure the course names match mock_selected_courses
    """
    modality_preferences = {
        'BIO-151': "LEC",
        'MAT-161': "LEC",
        'ENG-103': "LEC",
        'PSY-103': "LEC"
    }

    # Run this to ensure consistency between the selected courses and modality prefereces:  filter modality_preferences to include only the selected courses
    # return {course: modality_preferences.get(course, None) for course in selected_courses}

    # Runs this if you are confident that course names in modality preference matches course names in selected courses
    return modality_preferences

# For later
def mock_user_availability():
    """
    Mock function to simulate user availability for classes.
    """
    availability = {
        "Monday": ["8:00 AM - 11:00 PM"],
        "Tuesday": ["8:00 AM - 11:00 PM"],
        "Wednesday": ["8:00 AM - 11:00 PM"],
        "Thursday": ["8:00 AM - 11:00 PM"],
        "Friday": ["8:00 AM - 11:00 PM"],
        # Add more availability as needed
    }
    return availability

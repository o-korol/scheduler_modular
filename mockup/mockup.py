def mock_selected_courses():
    """
    Mock function to simulate user-selected courses.
    """
    selected_courses = ['BIO-151', 'MAT-143', 'ENG-103', 'PSY-103']
    # selected_courses = ['MAT-143']
    return selected_courses

def mock_modality_preferences():
    """
    Mock function to simulate user input for modality preferences.
    Note:  make sure the course names match mock_selected_courses
    """

    modality_preferences = {
        'BIO-151': "LEC",
        'MAT-143': "LEC",
        'ENG-103': "LEC",
        'PSY-103': "LEC"
    }

    """
    modality_preferences = {
        'MAT-143': "LEC",
    }
    """

    return modality_preferences

def mock_user_availability():
    """
    Mock function to simulate user availability for classes.
    """
    availability = {
        "M": ["7:00 AM - 11:00 PM"],
        "T": ["7:00 AM - 11:00 PM"],
        "W": ["7:00 AM - 11:00 PM"],
        "TH": ["7:00 AM - 11:00 PM"],
        "F": ["7:00 AM - 11:00 PM"],
        "S": ["11:00 AM - 10:00 PM"],
        "SU": []
    }
    return availability

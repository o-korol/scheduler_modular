from . import utils  # Import the entire utils module
from datetime import datetime  # Import datetime

@utils.time_function
def calculate_days_on_campus(combination, config):
    day_weights = config["day_weights"]
    selected_num_days = config["selected_num_days"]

    days_on_campus = set()
    for section in combination:
        if section["Method"] != "ONLIN":
            mtg_days = section["Mtg_Days"]
            if mtg_days:
                days_on_campus.update(mtg_days.split(', '))

    num_days = len(days_on_campus)

    if num_days > selected_num_days:
        penalty = day_weights.get(num_days, max(day_weights.values()))
    else:
        penalty = 0

    return penalty

@utils.time_function
def score_gaps(combination, config):
    """
    Calculate the gap score for a given combination.
    """
    gap_score = 0
    mandatory_break_start = datetime.strptime(config["gap_weights"]["mandatory_break_start"], '%I:%M %p').time()
    mandatory_break_end = datetime.strptime(config["gap_weights"]["mandatory_break_end"], '%I:%M %p').time()
    max_allowed_gap = config["gap_weights"]["max_allowed_gap"]
    penalty_per_hour = config["gap_weights"]["penalty_per_hour"]  # Get penalty rate from config

    # Initialize a dictionary to store sections by day
    day_sections_map = {day: [] for day in ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']}

    # Populate the day_sections_map with sections
    for section in combination:
        if section["STime"] and section["ETime"]:
            if section["Mtg_Days"]:
                for day in section["Mtg_Days"].split(','):
                    day = day.strip()  # Ensure no leading/trailing spaces
                    if day in day_sections_map:
                        day_sections_map[day].append({
                            "Name": section["Name"],
                            "STime": datetime.strptime(section["STime"], '%I:%M %p').time(),
                            "ETime": datetime.strptime(section["ETime"], '%I:%M %p').time(),
                            "Mtg_Days": day
                        })

    for day, day_sections in day_sections_map.items():
        # Check if there are sections before and after the mandatory break
        has_section_before = any(s["ETime"] <= mandatory_break_start for s in day_sections)
        has_section_after = any(s["STime"] >= mandatory_break_end for s in day_sections)

        # Add the mandatory break as a section for M, W, F if there are sections before and after the break
        if day in ['M', 'W', 'F'] and has_section_before and has_section_after:
            day_sections.append({
                "Name": "Mandatory Break",
                "STime": mandatory_break_start,
                "ETime": mandatory_break_end,
                "Mtg_Days": day
            })

        # Sort sections by start time
        day_sections.sort(key=lambda s: s["STime"])

        for i in range(1, len(day_sections)):
            prev_section = day_sections[i - 1]
            curr_section = day_sections[i]

            prev_end = prev_section["ETime"]
            curr_start = curr_section["STime"]

            gap_minutes = (datetime.combine(datetime.min, curr_start) - datetime.combine(datetime.min, prev_end)).seconds / 60

            if gap_minutes > max_allowed_gap:
                gap_hours = round(gap_minutes / 60)
                gap_score += gap_hours * penalty_per_hour  # Apply linear penalty

    return gap_score

@utils.time_function
def combined_score(combination, config):
    """
    Calculate the combined score for a combination based on modality, days, and gaps.
    """
    modality_score = 0  # Placeholder if modality score calculation is needed
    days_score = calculate_days_on_campus(combination, config)
    gap_score = score_gaps(combination, config)

    combined_score = (
        config["weights"]["days"] * days_score +
        config["weights"]["gaps"] * gap_score
    )
    return combined_score, days_score, gap_score

@utils.time_function
def score_combinations(combinations, config):
    scored_combinations = []
    for combination in combinations:
        try:
            combo_score, days_score, gap_score = combined_score(combination, config)
            scored_combinations.append((combination, combo_score, days_score, gap_score))
        except Exception as e:
            error_message = str(e)
            if 'score_combinations' not in utils.errors:
                utils.errors['score_combinations'] = set()
            if error_message not in utils.errors['score_combinations']:
                utils.errors['score_combinations'].add(error_message)
            print(f"Error scoring combination: {e}")

    scored_combinations.sort(key=lambda x: x[1])  # Sort by the combined score
    return scored_combinations

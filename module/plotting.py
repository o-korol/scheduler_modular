import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from .utils import time_function, parse_time
from .scoring import _extract_meeting_days
from datetime import datetime # Not used; superceded by parse_time

def split_text(text, max_width):
    """Split longer text to fit inside a course patch on the plot."""
    words = text.split(', ')
    lines = []
    current_line = words[0]
    for word in words[1:]:
        if len(current_line) + len(word) + 2 <= max_width:
            current_line += ', ' + word
        else:
            lines.append(current_line)
            current_line = word
    lines.append(current_line)
    return '\n'.join(lines)

def setup_axes(ax, days):
    """Set up the axes with grid lines and labels."""
    ax.set_xlim(-0.5, 6.5) # Set the x-axis limits to cover 7 days of the week
    ax.set_ylim(23, 7) # Set the y-axis limits to cover hours from 7 AM to 11 PM & invert them to make the plot look like a weekly planner page
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(7, 23))
    ax.set_yticklabels([f"{hour}:00" for hour in range(7, 23)])

    # Set up grid lines
    # (did not use default gridlines because they go through, not around, days on the x-axis)
    for i in range(len(days)):
        ax.axvline(x=i - 0.5, color='gray', linestyle='-', zorder=1)
    for hour in range(8, 23):
        ax.axhline(y=hour, color='gray', linestyle='-', zorder=1)

@time_function
def plot_schedule(schedule, option_number, scores):
    """Plot a schedule in a "weekly planner page" format.  Sections with no meeting time are plotted separately, below the weekly grid."""
    days = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']
    colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightsalmon', 'lightpink', 'lightseagreen', 'skyblue', 'lightgoldenrodyellow', 'lightcyan', 'lightgray']
    course_names = sorted(set(section['Course_Name'] for section in schedule)) # Sort sections alphabetically by course name
    color_map = {course: colors[i % len(colors)] for i, course in enumerate(course_names)} # Assign colors to courses, to maintain consistent color across different schedules

    fig, ax = plt.subplots(figsize=(14, 10))
    setup_axes(ax, days)

    no_meeting_times_sections = [] # Create and intialize a list to hold sections with no meeting times (e.g., ONLIN sections), to plot them separately

    for section in schedule:
        # Get section duration (full semester, 1st half, 2nd half, or partial).  If the info is missing, default to 'full semester'.
        duration = section.get('Duration', 'full semester').lower()
        # Set patch width and starting position on x axis, specified as offset from the vertical lines
        width, x_offset = {
            '1st half': (0.5, -0.5), # Modify patch width and x-axis position for half-semester sections
            '2nd half': (0.5, 0),
        }.get(duration, (1, -0.5)) # Specifiy default patch width and x-axis position values for default value ('full semester')

        start_time = parse_time(section['STime'])
        end_time = parse_time(section['ETime'])

        if not start_time or not end_time: # If section has no start time or end time, add to the list of sections that have no meeting times
            no_meeting_times_sections.append((section, width, x_offset))
            continue

        meeting_days = _extract_meeting_days(section)
        start_hour = start_time.hour + start_time.minute / 60 # convert time into a decimal for plotting
        end_hour = end_time.hour + end_time.minute / 60
        course_name = section['Course_Name']
        color = color_map.get(course_name, 'lightgrey')

        for day in meeting_days:
            if day not in days:
                continue

            day_index = days.index(day) # Convert days of the week to numbers for plotting (e.g., M = 0, T = 1, W = 2, etc.)
            # Specify the size and position of the patch:
            # (x, y) position of the upper left corner; width and length; aesthetics; front-to-back position (zorder)
            rect = patches.Rectangle((day_index + x_offset, start_hour), width, end_hour - start_hour, linewidth=1, edgecolor='black', facecolor=color, zorder=5)
            ax.add_patch(rect)
            split_name = split_text(section['Name'], max_width=15) # Split longer names to make them fit inside patches
            ax.text(day_index, (start_hour + end_hour) / 2, split_name, verticalalignment='center', horizontalalignment='center', zorder=6, fontsize=10)

    # Generate plot title dynamically, from the scores dictionary output by combined_score function in scoring module
    title_text = f'Schedule Option {option_number}\n' + ', '.join([f"{key.replace('_', ' ').title()}: {value}" for key, value in scores.items()])
    plt.title(title_text, zorder=10, fontsize=10) # Reduce font size to 10 to accomodate more scores.  Consider splitting the title text into multiple lines.

    if no_meeting_times_sections: # Plot sections with no meeting times at the bottom of the "weekly planner page"
        fig.subplots_adjust(bottom=0.2)
        online_ax = fig.add_axes([0.1, 0.05, 0.8, 0.1])
        online_ax.set_xlim(-0.5, 6.5)
        online_ax.set_ylim(0, len(no_meeting_times_sections))
        online_ax.axis('off')

        for index, (section, width, x_offset) in enumerate(no_meeting_times_sections):
            course_name = section['Course_Name']
            color = color_map.get(course_name, 'lightgrey')
            rect = patches.Rectangle((x_offset, index), width * 7, 1, linewidth=1, edgecolor='black', facecolor=color, zorder=5)
            online_ax.add_patch(rect)
            split_name = split_text(section['Name'], max_width=30)
            online_ax.text(3, index + 0.5, split_name, verticalalignment='center', horizontalalignment='center', zorder=6, fontsize=10)

    return fig

@time_function
def plot_schedules(combinations):
    """Plot top-N schedules & save them to a pdf."""
    with PdfPages('schedules.pdf') as pdf:
        top_N = 50 # Specify the number of top schedules to graph
        for i, (combination, scores) in enumerate(combinations[:top_N], start=1):
            fig = plot_schedule(combination, i, scores)
            pdf.savefig(fig)
            plt.close(fig)

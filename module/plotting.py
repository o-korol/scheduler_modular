import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages
from typing import List, Dict, Any, Tuple

from module.scoring import _extract_meeting_days
from module.utils import time_function, parse_time


def split_text(text: str, max_width: int) -> str:
    """
    Split longer text to fit inside a course patch on the plot.

    Args:
        text (str): The text to be split.
        max_width (int): The maximum width of the text in characters.

    Returns:
        str: The split text with line breaks.
    """
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


def setup_axes(ax: plt.Axes, days: List[str]) -> None:
    """
    Set up the axes, ticks, labels, and gridlines for the plot.

    Args:
        ax (matplotlib.axes.Axes): The axes to set up.
        days (list): The list of day labels.
    """
    ax.set_xlim(-0.5, 6.5)  # Set the x-axis limits to cover 7 days of the week
    # Set the y-axis limits to cover hours from 7 AM to 11 PM
    # Invert them to make the plot look like a weekly planner page
    ax.set_ylim(23, 7)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(7, 23))
    ax.set_yticklabels([f"{hour}:00" for hour in range(7, 23)])

    # Set up grid lines
    # Note:  Do not use default gridlines because they go through, not around, days on the x-axis
    for i in range(len(days)):
        ax.axvline(x=i - 0.5, color='gray', linestyle='-', zorder=1)
    for hour in range(8, 23):
        ax.axhline(y=hour, color='gray', linestyle='-', zorder=1)


@time_function
def plot_schedule(schedule: List[Dict[str, Any]],
                  option_number: int,
                  scores: Dict[str, Any]
) -> plt.Figure:
    """
    Plot a schedule in a "weekly planner page" format.
    Sections with no meeting time are plotted separately, below the weekly grid.

    Args:
        schedule (list): The list of sections to be plotted.
        option_number (int): The option number for the schedule.
        scores (dict): The scores associated with the schedule.

    Returns:
        matplotlib.figure.Figure: The figure object containing the plot.
    """
    days = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']
    colors = [
        'lightblue', 'lightcoral', 'lightgreen', 'lightsalmon', 'lightpink',
        'lightseagreen', 'skyblue', 'lightgoldenrodyellow', 'lightcyan', 'lightgray'
    ]
    # Sort sections alphabetically by course name
    course_names = sorted(set(section['Course_Name'] for section in schedule))
    # Assign colors to courses, to maintain consistent color across different schedules
    color_map = {course: colors[i % len(colors)] for i, course in enumerate(course_names)}

    fig, ax = plt.subplots(figsize=(14, 10))
    setup_axes(ax, days)

    # Create and intialize a list to hold sections with no meeting times
    # (e.g., ONLIN sections), to plot them separately
    no_meeting_times_sections = []

    for section in schedule:
        # Get section duration (full semester, 1st half, 2nd half, or partial).
        # If the info is missing, default to 'full semester'.
        duration = section.get('Duration', 'full semester').lower()
        # Set patch width and starting position on x axis, specified as offset from the vertical lines
        # Specifiy default patch width and x-axis position values for default value ('full semester')
        # Modify patch width and x-axis position for half-semester sections
        width, x_offset = {
            '1st half': (0.5, -0.5),
            '2nd half': (0.5, 0),
        }.get(duration, (1, -0.5))

        start_time = parse_time(section['STime'])
        end_time = parse_time(section['ETime'])

        # If section has no start time or end time, add to the list of sections that have no meeting times
        if not start_time or not end_time:
            no_meeting_times_sections.append((section, width, x_offset))
            continue

        meeting_days = _extract_meeting_days(section)
        # Convert time into a decimal for plotting
        start_hour = start_time.hour + start_time.minute / 60
        end_hour = end_time.hour + end_time.minute / 60
        course_name = section['Course_Name']
        color = color_map.get(course_name, 'lightgrey')

        for day in meeting_days:
            if day not in days:
                continue

            # Convert days of the week to numbers for plotting (e.g., M = 0, T = 1, etc.)
            day_index = days.index(day)
            # Specify characteristics of the patch
            rect = patches.Rectangle(
                (day_index + x_offset, start_hour),  # (x, y) position of the upper left corner
                width,
                end_hour - start_hour,  # length (y-axis dimension)
                linewidth=1,
                edgecolor='black',
                facecolor=color,
                zorder=5  # front-to-back position
            )
            ax.add_patch(rect)
            # Split longer names to make them fit inside patches
            split_name = split_text(section['Name'], max_width=15)
            ax.text(
                day_index,  # x-coordinate for the text position
                (start_hour + end_hour) / 2,  # y-coordinate for the text position
                split_name,  # text content to be displayed
                verticalalignment='center',
                horizontalalignment='center',
                zorder=6,
                fontsize=10
            )

    # Generate plot title dynamically,
    # from the scores dictionary output by combined_score function in scoring module
    title_text = (
        f'Schedule Option {option_number}\n' +
        ', '.join([
            f"{key.replace('_', ' ').title()}: {value}"
            for key, value in scores.items()
        ])
    )
    split_title_text = split_text(title_text, max_width=150)  # Width = number of characters
    plt.title(split_title_text, zorder=10)

    # Plot sections with no meeting times at the bottom of the "weekly planner page"
    if no_meeting_times_sections:
        fig.subplots_adjust(bottom=0.2)
        online_ax = fig.add_axes([0.1, 0.05, 0.8, 0.1])
        online_ax.set_xlim(-0.5, 6.5)
        online_ax.set_ylim(0, len(no_meeting_times_sections))
        online_ax.axis('off')

        for index, (section, width, x_offset) in enumerate(no_meeting_times_sections):
            course_name = section['Course_Name']
            color = color_map.get(course_name, 'lightgrey')
            rect = patches.Rectangle(
                (x_offset, index),
                width * 7,  # width = 7 * width of 1 day
                1,  # length
                linewidth=1,
                edgecolor='black',
                facecolor=color,
                zorder=5
            )
            online_ax.add_patch(rect)
            split_name = split_text(section['Name'], max_width=30)
            online_ax.text(
                3,  # x-coordinate for the text position
                index + 0.5,  # y-coordinate for the text position
                split_name,  # text content to be displayed
                verticalalignment='center',
                horizontalalignment='center',
                zorder=6,
                fontsize=10
            )
    return fig


@time_function
def plot_schedules(combinations: List[Tuple[List[Dict[str, Any]], Dict[str, Any]]]) -> None:
    """
    Plot top-N schedules & save them to a PDF file.

    Args:
        combinations (list): A list of tuples containing schedules and their scores.
    """
    # Specify pdf file name
    with PdfPages('schedules.pdf') as pdf:
        top_N = 50  # Specify the number of top schedules to graph
        for i, (combination, scores) in enumerate(combinations[:top_N], start=1):
            fig = plot_schedule(combination, i, scores)
            pdf.savefig(fig)
            plt.close(fig)

import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.backends.backend_pdf import PdfPages
from datetime import datetime
from .utils import time_function

@time_function
def plot_schedule(schedule, option_number, scores):
    days = ['M', 'T', 'W', 'TH', 'F', 'S', 'SU']
    colors = ['lightblue', 'lightcoral', 'lightgreen', 'lightsalmon', 'lightpink', 'lightseagreen', 'skyblue', 'lightgoldenrodyellow', 'lightcyan', 'lightgray']
    course_names = sorted(set(section['Course_Name'] for section in schedule))
    color_map = {course: colors[i % len(colors)] for i, course in enumerate(course_names)}

    fig, ax = plt.subplots(figsize=(14, 10))  # Adjust figure size if needed
    ax.set_xlim(-0.5, 6.5)
    ax.set_ylim(23, 7)
    ax.set_xticks(range(len(days)))
    ax.set_xticklabels(days)
    ax.set_yticks(range(7, 23))
    ax.set_yticklabels([f"{hour}:00" for hour in range(7, 23)])

    no_meeting_times_courses = []

    def split_text(text, max_width): # Split longer text to fit insde the course patch on the plot
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

    for section in schedule:
        if section['STime'] is None and section['ETime'] is None:
            no_meeting_times_courses.append(section)
        else:
            meeting_days = section['Mtg_Days'].split(', ') if section['Mtg_Days'] else []

            if section['STime'] and section['ETime']:
                start_time = datetime.strptime(section['STime'], '%I:%M %p').time()
                end_time = datetime.strptime(section['ETime'], '%I:%M %p').time()

                start_hour = start_time.hour + start_time.minute / 60
                end_hour = end_time.hour + end_time.minute / 60
                course_name = section['Course_Name']
                color = color_map.get(course_name, 'lightgrey')

                for day in meeting_days:
                    if day in days:
                        day_index = days.index(day)
                        rect = patches.Rectangle((day_index - 0.5, start_hour), 1, end_hour - start_hour, linewidth=1, edgecolor='black', facecolor=color, zorder=5)
                        ax.add_patch(rect)
                        split_name = split_text(section['Name'], max_width=15)
                        ax.text(day_index, (start_hour + end_hour) / 2, split_name, verticalalignment='center', horizontalalignment='center', zorder=6, fontsize=10)

    for i in range(len(days)):
        ax.axvline(x=i - 0.5, color='gray', linestyle='-', zorder=1)
    for hour in range(8, 23):
        ax.axhline(y=hour, color='gray', linestyle='-', zorder=1)

    # Generate the title dynamically from scores dictionary, passed to this function as 'scores'
    title_text = f'Schedule Option {option_number}\n' + ', '.join([f"{key.replace('_', ' ').title()}: {value}" for key, value in scores.items()])
    plt.title(title_text, zorder=10) # Higher z-order sends the text to the front

    if no_meeting_times_courses:
        fig.subplots_adjust(bottom=0.2)
        online_ax = fig.add_axes([0.1, 0.05, 0.8, 0.1])
        online_ax.set_xlim(-0.5, 6.5)
        online_ax.set_ylim(0, len(no_meeting_times_courses))
        online_ax.axis('off')

        for index, section in enumerate(no_meeting_times_courses):
            course_name = section['Course_Name']
            color = color_map.get(course_name, 'lightgrey')
            rect = patches.Rectangle((-0.5, index), 7, 1, linewidth=1, edgecolor='black', facecolor=color, zorder=5)
            online_ax.add_patch(rect)
            split_name = split_text(section['Name'], max_width=30)
            online_ax.text(3, index + 0.5, split_name, verticalalignment='center', horizontalalignment='center', zorder=6, fontsize=10)

    return fig

@time_function
def plot_schedules(combinations):
    with PdfPages('schedules.pdf') as pdf:
        for i, (combination, scores) in enumerate(combinations[:50], start=1):
            fig = plot_schedule(combination, i, scores)
            pdf.savefig(fig)
            plt.close(fig)

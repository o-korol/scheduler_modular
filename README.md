# Scheduler Modularized

This project is a modularized schedule optimizer that retrieves course information from a database, generates valid course combinations, calculates scores for each combination, and visualizes the schedules. The project is organized into several modules, each handling different aspects of the process.

## Project Structure

```
scheduler_modularized/
├── assets/
│   ├── cleaned_sample_schedule_SP24_6.csv
│   ├── generate_db.py
│   ├── sample_schedule_SP24_6.csv
│   ├── schedule.db
│   └── database_test_failures.csv
├── mockup/
│   ├── __init__.py
│   ├── mockup.py
├── module/
│   ├── __init__.py
│   ├── config.py
│   ├── database_operations.py
│   ├── plotting.py
│   ├── scheduling_logic.py
│   ├── scoring.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   ├── test_database_operations_all.py
│   ├── test_database_operations_one.py
├── main.py
└── README.md
```

## Installation

1. Clone the repository.
   ```sh
   git clone https://github.com/o-korol/scheduler_modularized.git
   cd scheduler_modularized
   ```

2. Install the required packages.
   ```sh
   pip install pandas
   ```

3. Ensure you have a working `schedule.db` database in the `assets` folder.  Alternatively, run generate_db.py, to generate the database from a .csv file included in the 'assets' folder.

## Usage

To run the main script, use:
```sh
python main.py
```

Course selection and modality preferences can be set in mockup.py.

## Running Tests

The project uses `unittest` for testing. To run the tests, use:
```sh
python -m unittest discover -s tests
```

## Modules

### 1. config.py
Contains configuration settings for the project, such as weights for scoring and day penalties.

### 2. database_operations.py
Handles database interactions, including retrieving course section information.

### 3. plotting.py
Contains functions for visualizing the generated schedules.

### 4. scheduling_logic.py
Contains the scheduling engine.  Generates valid course combinations, considering co-requisites and time conflicts.

### 5. scoring.py
Contains the scoring layer.  Calculates scores for each course combination based on criteria like number of days on campus, gaps between classes, and modality preferences.  Additional scores will be added soon (e.g., length of days, consistency between days).  Other scores will be added eventually (e.g., prioritizing sections with lowest enrollment).

### 6. utils.py
Contains utility functions used across multiple modules, such as time measurement and section grouping.

## Testing Details

### test_database_operations_all.py

This test script:
- Connects to the `schedule.db` database in the `assets` folder.
- Retrieves all unique course names.
- Tests `retrieve_section_info` for each course.
- Logs any errors or courses with empty dataframes into `database_test_failures.csv`.

### Example Output

```
course,error
AES-100,Dataframe is unexpectedly empty for course: AES-100
...
```

## Notes

- Ensure that `schedule.db` is updated with the latest course information.
- The `database_test_failures.csv` file will contain details of any test failures for further inspection.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License.

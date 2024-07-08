# Scheduler Modular

This project is a modularized schedule optimizer that retrieves course information from a database, generates valid course combinations, calculates scores for each combination, and visualizes the schedules. The project is organized into several modules.

## Project Structure

```
scheduler_modularized/
├── assets/
│   ├── cleaned_sample_schedule_SP24_6.csv
│   ├── generate_db.py
│   ├── sample_schedule_SP24_6.csv
│   └── schedule.db  
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
│   ├── conftest.py
│   ├── test_database_operations.py
│   ├── test_scheduling_logic.py
│   ├── test_scoring.py
│   └── test_utils.py
├── main.py
├── README.md
└── schedules.pdf
```

## Installation

1. Clone the repository.
   ```sh
   git clone https://github.com/o-korol/scheduler_modular.git
   cd scheduler_modular
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
To see top-ranked schedules, open schedules.pdf.

## Running Tests

The project uses `pytest` for testing.

For testing, install pytest:
   ```sh
   pip install pytest
   ```
To run tests, switch to tests directory and run pytest:

   ```sh
   cd tests
   tests/ $ pytest
   ```

## Modules

### 1. config.py
Contains configuration settings for the project, such as weights for scoring and penalties.

### 2. database_operations.py
Handles database interactions, including retrieving course section information.

### 3. plotting.py
Contains functions for visualizing the generated schedules.

### 4. scheduling_logic.py
Contains the scheduling engine.  Generates valid course combinations, considering co-requisites and time conflicts.

### 5. scoring.py
Contains the scoring layer.  Calculates scores for each course combination based on criteria like number of days on campus, gaps between classes, modality preferences, length of days, and consistency between days.  Other scores will be added eventually (e.g., prioritizing sections with the lowest enrollment).

### 6. utils.py
Contains utility functions used across multiple modules, such as time measurement and section grouping.

## Notes

- Ensure that `schedule.db` is updated with the latest course information.
- The `database_test_failures.csv` file will contain details of any test failures for further inspection.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License.

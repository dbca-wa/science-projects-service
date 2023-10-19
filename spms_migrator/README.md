SPMS Migrator
-----
This project is designed to assist with the ETL process for 'SPMS' migrations at DBCA. It is a CLI program which utilises Python and Pandas, and the functionality and design are based on https://github.com/idabblewith/Python100.


### Structure
  ```sh
  ├── README.md 
  ├── Start.py
  ├── ChoiceViewer.py 
  ├── ChoiceLauncher.py 
  ├── FileHandler.py 
  ├── Extractor.py 
  ├── Transformer.py 
  ├── Loader.py 
  ├── misc.py *** Various helper functions
  ├── gitignore *** Ignored files list
  ├── gitattributes *** Attributes for git
  ├── pyproject.toml *** The dependencies which will be loaded with "poetry shell"
  ├── poetry.lock *** If not present, will appear when you run poetry
  └── data
      ├── raw_data
      ├── modded_data
      ├── clean_data
  ```


### Core classes:
There are 7:
* Extractor: Handles the logic for extracting data from a source
* Transformer: Handles the logic for transforming data in a directory
(directory is either `{project_dir}/raw_data` or `{project_dir}/modded_data`)
* Loader: Handles logic for loading data into a specified destination database
* File Handler: Handles the logic for dealing with files and data frames
* Choice Viewer: Handles the logic for displaying and selecting operation/function choices for the selected project and category (E, T, or L)
* Choice Launcher: Handles the logic for performing the selected operation
* Start: Handles the logic for running the entire program. You will call
py Start.py from the root directory to run the program.


---

## How To and Requirements:


### To Extract data: 
You will need to set a source database and have access to that database from the computer running the script. You can set this by editng the code in Extractor.py under self.db_source.

### To Transform: 
You will need the csv files - you cannot perform operations on files that do not exist. By default all csv files are gitignored, so you must either use the Extract functions or manually populate the data/raw_data folder with the csv data you would like to manipulate.

### To Load: 
You will need to set the target database for the project. You can set this by editng the code in Loader.py under self.db_destination.

### To Run Program Locally: 
All of the above, plus the following steps:
1) Install Poetry if not already installed (See https://python-poetry.org/docs/)
2) Go to the root directory of the project.
3) Run 
```
poetry shell
```
4) cd back into the root directory if you have been moved away by running the poetry command
5) Run 
```py Start.py```
6) Follow the prompts and run operations.


---

## Example

This is an example of running the "Clean HTML" generic function.

1) Run the program 
```py Start.py```
2) Select the 'Transform' category by typing '2' and pressing enter
![Transform](https://github.com/idabblewith/SPMS_Migrator/blob/main/media/select_operation.png?raw=true)
3) Select Clean HTML by typing the corresponding number and pressing enter (2 in this case)
![Function](https://github.com/idabblewith/SPMS_Migrator/blob/main/media/select_function.png?raw=true)
4) You will be prompted with an option to batch clean:
    a) If you would not like to batch clean, press enter. Then type the number corresponding to the file you wish to clean.
    b) If you would like to batch clean files in the spms_data/raw_data folder, type 'y'.
5) The program will run its magic to clean the HTML file/files
*BATCH VERSION:*
![Batch](https://github.com/idabblewith/SPMS_Migrator/blob/main/media/batch_clean.png?raw=true)
*SINGLE FILE VERSION:*
![Single](https://github.com/idabblewith/SPMS_Migrator/blob/main/media/single_clean.png?raw=true)


---

## Existing Functions


* (General) Clean HTML: Removes HTML from a sepecified file/dataframe
* (SPMS) Remove Columns: Removes specified columns from a specified file/dataframe
* (SPMS) Remove No Changes Entries: Removes "No changes made." rows from csv files as empty data.
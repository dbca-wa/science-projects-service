from bs4 import BeautifulSoup, MarkupResemblesLocatorWarning
from FileHandler import FileHandler
import warnings
import time


class Transformer:
    def __init__(self, file_handler, misc, tqdm, pd):
        self.pd = pd
        self.tqdm = tqdm
        self.misc = misc
        self.file_handler = file_handler
        self.selected_batch = None
        self.selected_file = self.file_handler.selected_file
        self.df = None
        self.functions = [
            {
                "name": "Run All",
                "function": self.spms_run_all,
            },
            {
                "name": "Remove Columns",
                "function": self.spms_remove_columns_from_selected_df,
            },
            {
                "name": "Remove Null Entries",
                "function": self.spms_remove_null_entries,
            },
            {
                "name": "Clean HTML",
                "function": self.clean_html,
            },
        ]

    # HELPER FUNCTIONS START ======================================================================================

    def determine_folder_and_return_files(self):
        mod_dir = self.misc.nli("Use modded folder files?")
        directory = ""
        if mod_dir in self.misc.yes_array:
            files = self.file_handler.get_modded_files_for_batch()
            directory = self.file_handler.modded_directory
        else:
            files = self.file_handler.get_raw_files_for_batch()
            directory = self.file_handler.raw_directory
        return files, directory

    def continue_operations_on_modded_file(self, selected_file, df):
        continue_with_this_file = self.misc.nli(
            f"Continue transform operations with {selected_file}??\nType 'y' for yes, or 'n' for no."
        )

        if continue_with_this_file in self.misc.yes_array:
            self.selected_file = selected_file
            self.file_handler.selected_file = selected_file
            self.misc.nls(
                f"{self.misc.bcolors.OKBLUE}Continuing with File{selected_file}{self.misc.bcolors.ENDC}"
            )
            self.df = df
            self.misc.nli(
                f"{self.misc.bcolors.OKBLUE}Continuing with Dataframe for {selected_file}. Press any key.{self.misc.bcolors.ENDC}"
            )
            # self.misc.cls()
            # return
        else:
            self.selected_file = None
            self.df = None
            # return

    def continue_operations_on_modded_batch(self, files, continous=False):
        if continous == True:
            self.selected_batch = files
            self.file_handler.selected_batch = files
            # self.misc.nli(self.selected_batch)
            self.misc.nls(
                f"{self.misc.bcolors.OKBLUE}Continuing with this batch{self.misc.bcolors.ENDC}"
            )

        else:
            continue_with_this_batch = self.misc.nli(
                f"Continue transform operations with this batch??\nType 'y' for yes, or 'n' for no."
            )
            if continue_with_this_batch in self.misc.yes_array:
                self.selected_batch = files
                self.file_handler.selected_batch = files
                self.misc.nls(
                    f"{self.misc.bcolors.OKBLUE}Continuing with this batch{self.misc.bcolors.ENDC}"
                )
                # self.df = df
                # self.misc.nli(
                #     f"{self.misc.bcolors.OKBLUE}Continuing with Dataframe for {selected_file}. Press any key.{self.misc.bcolors.ENDC}"
                # )
                # self.misc.cls()
                # return
            else:
                self.selected_batch = None
                self.file_handler.selected_batch = None
                self.selected_file = None
                self.df = None
                # return

    def reset_file_and_df(self):
        self.selected_file = None
        self.df = None
        self.file_handler.selected_file = None

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds %= 60
        milliseconds = int((seconds - int(seconds)) * 1000)
        seconds = int(seconds)

        time_parts = []

        if minutes > 0:
            # Use 'min' instead of 'mins' if minutes is less than 2
            minutes_str = f"{minutes} min" if minutes < 2 else f"{minutes} mins"
            time_parts.append(minutes_str)

        if seconds > 0:
            # Use 'second' instead of 'seconds' if seconds is less than 2
            seconds_str = f"{seconds} second" if seconds < 2 else f"{seconds} seconds"
            time_parts.append(seconds_str)

        if milliseconds > 0 and minutes <= 1:
            # Use 'millisecond' instead of 'milliseconds' if milliseconds is less than 2
            milliseconds_str = (
                f"{milliseconds} millisecond"
                if milliseconds < 2
                else f"{milliseconds} milliseconds"
            )
            time_parts.append(milliseconds_str)

        time_string = ", ".join(time_parts)

        return f"{self.misc.bcolors.ENDC}{self.misc.bcolors.OKGREEN}{time_string}{self.misc.bcolors.ENDC}{self.misc.bcolors.OKBLUE}"

    # HELPER FUNCTIONS END ======================================================================================

    # GENERAL FUNCTIONS START ======================================================================================

    def test(self):
        print(self.selected_file)

    def clean_html(self, continue_with_batch=False, batch_files=[]):
        def remove_html_and_newlines(input_string):
            if isinstance(input_string, str):
                soup = BeautifulSoup(input_string, "html.parser")
                text_without_html = soup.get_text()
                without_newlines = text_without_html.replace("\n", "")
                return without_newlines
            return input_string

        if continue_with_batch == False:
            batch_clean = self.misc.nli("Batch clean HTML?")
            start_time = time.time()

            # If not batch cleaning
            if batch_clean not in self.misc.yes_array:
                # If continuing with a selected file
                if self.selected_file != "" and self.selected_file != None:
                    # Use existing file and df
                    selected_file = self.selected_file
                    df = self.df

                    print(
                        f"==============================================================\n\nWORKING ON {self.selected_file}"
                    )
                    # Remove HTML tags from string columns
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore", category=MarkupResemblesLocatorWarning
                        )
                        df = df.applymap(remove_html_and_newlines)

                    # Save the file and print the time
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=selected_file,
                        new_location=self.file_handler.modded_directory,
                    )
                    elapsed_time = time.time() - start_time

                    self.misc.nls(msg)

                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}HTML FREE VERSION CREATED IN {self.format_time(elapsed_time)}!{self.misc.bcolors.ENDC}."
                    )

                # If NOT continuing with a selected file
                else:
                    # Determine folder to look in
                    _, directory = self.determine_folder_and_return_files()
                    # Review files in the raw_data directory
                    selected_file = self.file_handler.display_files_in_directory(
                        directory=directory,
                    )
                    start_time = time.time()

                    # Read the CSV file into a DataFrame
                    df = self.file_handler.read_csv_and_prepare_df(selected_file)
                    self.file_handler.display_file_being_worked_on(selected_file)

                    # Remove HTML tags from string columns
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore", category=MarkupResemblesLocatorWarning
                        )
                        df = df.applymap(
                            lambda x: BeautifulSoup(x, "html.parser").get_text()
                            if isinstance(x, str)
                            else x
                        )

                    # Save the file and print the time
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=selected_file,
                        new_location=self.file_handler.modded_directory,
                    )
                    elapsed_time = time.time() - start_time

                    self.misc.nls(msg)

                    self.misc.nls(
                        f"{self.misc.bcolors.OKGREEN}HTML FREE VERSION CREATED IN {self.format_time(elapsed_time)}!{self.misc.bcolors.ENDC}."
                    )

                    # Determine if should continue operations with selected df and file
                    self.continue_operations_on_modded_file(selected_file, df)

            # If batch cleaning HTML
            else:
                # Select directory to clean
                files, _ = self.determine_folder_and_return_files()

                updated_files = []
                # Batch clean
                for file in self.tqdm(
                    files,
                    unit="file",
                    desc="Processing files",
                    bar_format="{desc}: {bar}",
                ):
                    self.file_handler.display_file_being_worked_on(file)
                    file_start_time = time.time()
                    df = self.file_handler.read_csv_and_prepare_df(file)
                    # self.df = df
                    with warnings.catch_warnings():
                        warnings.filterwarnings(
                            "ignore", category=MarkupResemblesLocatorWarning
                        )
                        df = df.applymap(remove_html_and_newlines)

                    selected_file, _ = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=file,
                        new_location=self.file_handler.modded_directory,
                    )
                    updated_files.append(selected_file)
                    fin_time = time.time() - file_start_time
                    self.misc.nls(
                        f"{self.misc.bcolors.OKBLUE}HTML FREE VERSION CREATED IN {self.format_time(fin_time)}! SEE {selected_file}.{self.misc.bcolors.ENDC}"
                    )
                elapsed_time = time.time() - start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Batch cleaning completed in {self.format_time(elapsed_time)}!{self.misc.bcolors.ENDC}"
                )

                self.reset_file_and_df()
                self.continue_operations_on_modded_batch(files=updated_files)

        else:
            # Batch clean
            start_time = time.time()
            updated_files = []
            skip_files = [
                "./data/raw_data\documents_conceptplan.csv",
                "./data/raw_data\documents_projectplan.csv",
                "./data/raw_data\documents_progressreport.csv",
                "./data/raw_data\documents_studentreport.csv",
                "./data/raw_data\documents_projectclosure.csv",
                "./data/modded_data\documents_conceptplan.csv",
                "./data/modded_data\documents_projectplan.csv",
                "./data/modded_data\documents_progressreport.csv",
                "./data/modded_data\documents_studentreport.csv",
                "./data/modded_data\documents_projectclosure.csv",
            ]
            for file in self.tqdm(
                batch_files,
                unit="file",
                desc="Processing files",
                bar_format="{desc}: {bar}",
            ):
                if file in skip_files:
                    print(
                        f"{self.misc.bcolors.WARNING}==============================================================\n\SKIPPING {file}{self.misc.bcolors.ENDC}"
                    )
                    continue
                print(
                    f"==============================================================\n\nWORKING ON HTML of {file}"
                )
                file_start_time = time.time()

                df = self.file_handler.read_csv_and_prepare_df(file)
                # self.df = df
                with warnings.catch_warnings():
                    warnings.filterwarnings(
                        "ignore", category=MarkupResemblesLocatorWarning
                    )
                    df = df.applymap(remove_html_and_newlines)

                selected_file, _ = self.file_handler.save_df_as_csv(
                    df=df,
                    selected_file=file,
                    new_location=self.file_handler.modded_directory,
                )
                updated_files.append(selected_file)
                fin_time = time.time() - file_start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKBLUE}HTML FREE VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                )
            elapsed_time = time.time() - start_time
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Batch cleaning completed in {self.format_time(elapsed_time)}! Modified files are in the modded_data folder.{self.misc.bcolors.ENDC}"
            )

            self.reset_file_and_df()
            self.continue_operations_on_modded_batch(
                files=updated_files, continous=True
            )

    # GENERAL FUNCTIONS END ======================================================================================

    # SPMS FUNCTIONS START ======================================================================================

    def spms_run_all(self):
        # input("NOT YET IMPLEMENTED. PRESS ENTER TO CONTINUE.")
        start_time = time.time()
        self.selected_batch = self.file_handler.get_raw_files_for_batch()
        self.spms_remove_columns_from_selected_df(
            continue_with_batch=True, batch_files=self.selected_batch
        )
        self.spms_remove_null_entries(
            continue_with_batch=True, batch_files=self.selected_batch
        )
        self.clean_html(continue_with_batch=True, batch_files=self.selected_batch)
        # self.misc.cls()
        elapsed_time = self.format_time(time.time() - start_time)
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Moving files to clean directory...{self.misc.bcolors.ENDC}"
        )
        self.file_handler.move_modded_to_clean_on_continuous_batch_completion()
        self.misc.nls(
            f"{self.misc.bcolors.OKGREEN}Complete! Entire operation took {elapsed_time} to complete.{self.misc.bcolors.ENDC}"
        )
        self.misc.nli(f"{self.misc.bcolors.WARNING}Press enter to continue.")

    def spms_remove_null_entries(self, continue_with_batch=False, batch_files=[]):
        # start_time = time.time()
        if continue_with_batch == False:
            batch_remove_nulls = self.misc.nli("Batch remove Null entries?")
            start_time = time.time()

            # If not batch running
            if batch_remove_nulls not in self.misc.yes_array:
                # If continuing with a selected file
                if self.selected_file != "" and self.selected_file != None:
                    # Use existing file and df
                    selected_file = self.selected_file
                    df = self.df
                    self.file_handler.display_file_being_worked_on(selected_file)

                    # Main operation (removing rows with "No changes made.")
                    if "comment" in df.columns:
                        df = df[df["comment"] != "No fields changed."]

                    # Saving files
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=file,
                        new_location=self.file_handler.modded_directory,
                    )

                    # Calculate time for file and display
                    fin_time = time.time() - file_start_time
                    self.misc.nls(
                        f"{self.misc.bcolors.OKBLUE}NO COMMENT ENTRY REMOVED VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                    )

                # If there is no selected file/data_frame saved to the instance
                else:
                    # Determine folder to look in
                    _, directory = self.determine_folder_and_return_files()
                    # Review files in the raw_data directory
                    selected_file = self.file_handler.display_files_in_directory(
                        directory=directory,
                    )
                    start_time = time.time()
                    self.file_handler.display_file_being_worked_on(selected_file)
                    # Read the CSV file into a DataFrame
                    print("reading csv into df...")
                    df = self.file_handler.read_csv_and_prepare_df(selected_file)

                    # Main operation (removing rows with "No changes made.")
                    if "comment" in df.columns:
                        df = df[df["comment"] != "No fields changed."]

                    # Saving files
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=file,
                        new_location=self.file_handler.modded_directory,
                    )

                    # Calculate time for file and display
                    fin_time = time.time() - file_start_time
                    self.misc.nls(
                        f"{self.misc.bcolors.OKBLUE}NULL ENTRY VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                    )

                self.misc.nls(msg)
                self.continue_operations_on_modded_file(
                    selected_file=selected_file, df=df
                )

            # If batch cleansing "No changes made" entries
            else:
                # Select directory to clean
                files, _ = self.determine_folder_and_return_files()
                updated_files = []
                start_time = time.time()

                # Logic per file in directory
                for file in self.tqdm(
                    files,
                    unit="file",
                    desc="Processing files",
                    bar_format="{desc}: {bar}",
                ):
                    self.file_handler.display_file_being_worked_on(file)
                    file_start_time = time.time()
                    df = self.file_handler.read_csv_and_prepare_df(file)

                    # Main operation (removing rows with "No changes made.")
                    if "comment" in df.columns:
                        df = df[df["comment"] != "No fields changed."]

                    # Saving files
                    selected_file = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=file,
                        new_location=self.file_handler.modded_directory,
                    )
                    updated_files.append(selected_file)

                    # Calculate time for file and display
                    fin_time = time.time() - file_start_time
                    self.misc.nls(
                        f"{self.misc.bcolors.OKBLUE}NULL ENTRY VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                    )

                # Calculate total time and display
                elapsed_time = time.time() - start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Batch cleaning completed in {self.format_time(elapsed_time)}! Modified files are in the modded_data folder.{self.misc.bcolors.ENDC}"
                )

                self.continue_operations_on_modded_batch(files=updated_files)
                self.reset_file_and_df()
        else:
            start_time = time.time()
            updated_files = []
            # Logic per file in directory
            for file in self.tqdm(
                batch_files,
                unit="file",
                desc="Processing files",
                bar_format="{desc}: {bar}",
            ):
                print(
                    f"==============================================================\n\nWORKING ON {file}"
                )
                file_start_time = time.time()
                df = self.file_handler.read_csv_and_prepare_df(file)

                # Main operation (removing rows with "No changes made.")
                if "comment" in df.columns:
                    df = df[df["comment"] != "No fields changed."]

                # Saving files
                selected_file, _ = self.file_handler.save_df_as_csv(
                    df=df,
                    selected_file=file,
                    new_location=self.file_handler.modded_directory,
                )
                updated_files.append(selected_file)

                # Calculate time for file and display
                fin_time = time.time() - file_start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKBLUE}NULL ENTRY VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                )

            # Calculate total time and display
            elapsed_time = time.time() - start_time
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Batch cleaning completed in {self.format_time(elapsed_time)}! Modified files are in the modded_data folder.{self.misc.bcolors.ENDC}"
            )

            self.reset_file_and_df()
            self.continue_operations_on_modded_batch(
                files=updated_files,
                continous=True,
            )

    def spms_remove_columns_from_selected_df(
        self, continue_with_batch=False, batch_files=[]
    ):
        columns_to_exclude = [
            "effective_from",
            "effective_to",
            "creator_id",
            "modifier_id",
            "created",
            "modified",
        ]

        if continue_with_batch == False:
            # List of columns to exclude
            batch_remove_columns = self.misc.nli("Batch remove columns?")
            start_time = time.time()

            # If not batch removing
            if batch_remove_columns not in self.misc.yes_array:
                # If there is a selected data_frame already and we are continuing with a file
                if self.df != None and self.df != "":
                    # Drop the columns
                    print("dropping columns...")
                    selected_file = self.selected_file
                    self.file_handler.display_file_being_worked_on(selected_file)
                    print(selected_file)
                    if selected_file.endswith("projects_project.csv"):
                        df = self.df.drop(
                            columns=[
                                "polymorphic_ctype_id",
                                "effective_from",
                                "effective_to",
                                "position",
                            ],
                            errors="ignore",
                        )
                    elif "documents" in selected_file:
                        columns_to_exclude = [
                            "polymorphic_ctype_id",
                            "effective_from",
                            "effective_to",
                            "position",
                        ]
                        columns_to_drop = [
                            col for col in columns_to_exclude if col in self.df.columns
                        ]
                        df = self.df.drop(columns=columns_to_drop, errors="ignore")
                    else:
                        df = self.df.drop(columns=columns_to_exclude, errors="ignore")

                    # Save the file
                    print("saving...")
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=self.selected_file,
                        new_location=self.file_handler.modded_directory,
                    )

                    elapsed_time = time.time() - start_time
                    # Print time to complete
                    self.misc.nli(
                        f"{self.misc.bcolors.OKBLUE}Columns dropped in {self.format_time(elapsed_time)}!{self.misc.bcolors.ENDC}"
                    )

                # If there is no selected file/data_frame saved to the instance
                else:
                    # Determine folder to look in
                    _, directory = self.determine_folder_and_return_files()
                    # Review files in the raw_data directory
                    selected_file = self.file_handler.display_files_in_directory(
                        directory=directory,
                    )
                    self.file_handler.display_file_being_worked_on(selected_file)
                    start_time = time.time()

                    # Read the CSV file into a DataFrame
                    print("reading csv into df...")
                    df = self.file_handler.read_csv_and_prepare_df(selected_file)

                    # Drop the columns
                    print("dropping columns...")
                    if selected_file.endswith("projects_project.csv"):
                        df = self.df.drop(
                            columns=[
                                "polymorphic_ctype_id",
                                "effective_from",
                                "effective_to",
                                "position",
                            ],
                            errors="ignore",
                        )
                    elif "documents" in selected_file:
                        columns_to_exclude = [
                            "polymorphic_ctype_id",
                            "effective_from",
                            "effective_to",
                            "position",
                        ]
                        columns_to_drop = [
                            col for col in columns_to_exclude if col in self.df.columns
                        ]
                        df = self.df.drop(columns=columns_to_drop, errors="ignore")
                    else:
                        df = self.df.drop(columns=columns_to_exclude, errors="ignore")

                    # Save the file
                    print("saving...")
                    selected_file, msg = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=selected_file,
                        new_location=self.file_handler.modded_directory,
                    )

                    elapsed_time = time.time() - start_time
                    # Print time to complete
                    self.misc.nli(
                        f"{self.misc.bcolors.OKBLUE}Columns dropped in {self.format_time(elapsed_time)}! Press any key.{self.misc.bcolors.ENDC}"
                    )

                self.misc.nls(msg)

                self.continue_operations_on_modded_file(
                    selected_file=selected_file, df=df
                )

            # If batch removing
            else:
                # Select directory to clean
                files, _ = self.determine_folder_and_return_files()
                updated_files = []

                for file in self.tqdm(
                    files,
                    unit="file",
                    desc="Processing files",
                    bar_format="{desc}: {bar}",
                ):
                    self.file_handler.display_file_being_worked_on(file)
                    file_start_time = time.time()
                    selected_file = file
                    print(selected_file)
                    self.df = self.file_handler.read_csv_and_prepare_df(selected_file)
                    if selected_file.endswith("projects_project.csv"):
                        df = self.df.drop(
                            columns=[
                                "polymorphic_ctype_id",
                                "effective_from",
                                "effective_to",
                                "position",
                            ],
                            errors="ignore",
                        )
                    elif "documents" in selected_file:
                        columns_to_exclude = [
                            "polymorphic_ctype_id",
                            "effective_from",
                            "effective_to",
                            "position",
                        ]
                        columns_to_drop = [
                            col for col in columns_to_exclude if col in self.df.columns
                        ]
                        df = self.df.drop(columns=columns_to_drop, errors="ignore")
                    else:
                        df = self.df.drop(columns=columns_to_exclude, errors="ignore")

                    # Saving files
                    selected_file = self.file_handler.save_df_as_csv(
                        df=df,
                        selected_file=file,
                        new_location=self.file_handler.modded_directory,
                    )
                    updated_files.append(selected_file)

                    # Calculate time for file and display
                    fin_time = time.time() - file_start_time
                    self.misc.nls(
                        f"{self.misc.bcolors.OKBLUE}COLUMN-DROPPED VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                    )
                elapsed_time = time.time() - start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKGREEN}Batch column drop completed in {self.format_time(elapsed_time)}! Modified files are in the modded_data folder.{self.misc.bcolors.ENDC}"
                )

                self.continue_operations_on_modded_batch(files=updated_files)
                self.reset_file_and_df()
        else:
            start_time = time.time()
            updated_files = []
            for file in self.tqdm(
                batch_files,
                unit="file",
                desc="Processing files",
                bar_format="{desc}: {bar}",
            ):
                print(
                    f"==============================================================\n\nWORKING ON {file}"
                )
                file_start_time = time.time()
                selected_file = file
                print(selected_file)
                self.df = self.file_handler.read_csv_and_prepare_df(selected_file)
                if selected_file.endswith("projects_project.csv"):
                    df = self.df.drop(
                        columns=[
                            "polymorphic_ctype_id",
                            "effective_from",
                            "effective_to",
                            # "position",
                        ],
                        errors="ignore",
                    )
                elif "documents" in selected_file:
                    columns_to_exclude = [
                        "polymorphic_ctype_id",
                        "effective_from",
                        "effective_to",
                        "position",
                    ]
                    columns_to_drop = [
                        col for col in columns_to_exclude if col in self.df.columns
                    ]
                    df = self.df.drop(columns=columns_to_drop, errors="ignore")
                else:
                    df = self.df.drop(columns=columns_to_exclude, errors="ignore")

                # df = df.drop(columns=columns_to_exclude, errors="ignore")

                # Saving files
                selected_file, _ = self.file_handler.save_df_as_csv(
                    df=df,
                    selected_file=file,
                    new_location=self.file_handler.modded_directory,
                )
                updated_files.append(selected_file)

                # Calculate time for file and display
                fin_time = time.time() - file_start_time
                self.misc.nls(
                    f"{self.misc.bcolors.OKBLUE}COLUMN-DROPPED VERSION CREATED IN {self.format_time(fin_time)}!{self.misc.bcolors.ENDC}"
                )

            # Calculate total time and display
            elapsed_time = time.time() - start_time
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}Batch column drop completed in {self.format_time(elapsed_time)}! Modified files are in the modded_data folder.{self.misc.bcolors.ENDC}"
            )

            self.reset_file_and_df()
            # input("here")
            self.continue_operations_on_modded_batch(
                files=updated_files,
                continous=True,
            )

    # SPMS FUNCTIONS END ======================================================================================

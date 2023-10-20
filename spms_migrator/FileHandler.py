class FileHandler:
    def __init__(
        self,
        project,
        pd,
        os,
        misc,
        #  shutil,
        tqdm,
    ):
        self.tqdm = tqdm
        self.misc = misc
        # self.shutil = shutil
        self.pd = pd
        self.os = os
        self.project = project
        self.base_directory = ""
        self.determine_base_directory = self.get_base_directory(project)
        self.determine_base_directory = self.get_source_db(project)
        self.determine_base_directory = self.get_destination_db(project)
        self.raw_directory = f"./{self.base_directory}/raw_data"
        self.modded_directory = f"./{self.base_directory}/modded_data"
        self.clean_directory = f"./{self.base_directory}/clean_data"
        self.source_db = ""
        self.destination_db = ""
        self.selected_file = ""
        self.selected_batch = None
        self.functions = [
            {
                "name": "Display Files in Directory",
                "function": self.display_files_in_directory,
            },
        ]

    def display_file_being_worked_on(self, file):
        print(
            f"==============================================================\n\nWORKING ON {file}"
        )

    def get_base_directory(self, project):
        dir = "data"
        self.base_directory = dir
        print(
            f"{self.misc.bcolors.OKGREEN}File Handler:{self.misc.bcolors.ENDC} {self.misc.bcolors.OKBLUE}Base dir set to: {self.base_directory}.{self.misc.bcolors.ENDC}"
        )

    def get_source_db(self, project):
        db = ""
        if project == "SPMS":
            db = "SOURCE DB NOT YET IMPLEMENTED"
        elif project == "SPECIFY":
            db = "SOURCE DB NOT YET IMPLEMENTED"

        if not db == "SOURCE DB NOT YET IMPLEMENTED":
            self.source_db = db
            print(
                f"{self.misc.bcolors.FAIL}File Handler:{self.misc.bcolors.ENDC} {self.misc.bcolors.OKBLUE}Source DB set to: {self.source_db}.{self.misc.bcolors.ENDC}"
            )
        else:
            print(
                f"{self.misc.bcolors.FAIL}File Handler:{self.misc.bcolors.ENDC} {self.misc.bcolors.WARNING}{db}. Some functions may not work.{self.misc.bcolors.ENDC}"
            )
            self.db = ""

    def get_destination_db(self, project):
        db = ""
        if project == "SPMS":
            db = "DESTINATION DB NOT YET IMPLEMENTED"
        elif project == "SPECIFY":
            db = "DESTINATION DB NOT YET IMPLEMENTED"

        if not db == "DESTINATION DB NOT YET IMPLEMENTED":
            self.destination_db = db
            print(
                f"{self.misc.bcolors.FAIL}File Handler:{self.misc.bcolors.ENDC} {self.misc.bcolors.OKBLUE}Destination DB set to: {self.destination_db}.{self.misc.bcolors.ENDC}\n"
            )
        else:
            print(
                f"{self.misc.bcolors.FAIL}File Handler:{self.misc.bcolors.ENDC} {self.misc.bcolors.WARNING}{db}. Some functions may not work.{self.misc.bcolors.ENDC}\n"
            )
            self.db = ""

    def print_selected_file(self):
        print(self.selected_file)

    def display_files_in_directory(self, directory):
        files = self.os.listdir(directory)
        num_columns = (len(files) + 3) // 4
        num_rows = 10

        # Create a 2D list to store the file names in the desired format
        new_list = [
            [
                files[row + col * num_rows]
                if row + col * num_rows < len(files)
                else None
                for row in range(num_rows)
            ]
            for col in range(num_columns)
        ]

        if not new_list:
            print("No files available.")
            return None

        col_width = (
            max(len(file) for row in new_list for file in row if file is not None) + 6
        )  # padding

        print("FILES AVAILABLE IN DIRECTORY:")
        print()
        for row in range(num_rows):
            for col in range(num_columns):
                file = new_list[col][row]
                if file is not None:
                    index = row + col * num_rows + 1
                    formatted_file = (
                        f"{index}. {file[:20] + '...' if len(file) > 15 else file}"
                    )
                    print(formatted_file.ljust(col_width), end="")
            print()
        print()
        selected_file = self.select_file_from_display(directory=directory, files=files)
        while selected_file == None:
            selected_file = self.select_file_from_display(
                directory=directory, files=files
            )

        return selected_file

    def select_file_from_display(self, directory, files):
        selected_file = input("Enter the number of the file you want to select: ")
        try:
            selected_index = int(selected_file) - 1
            if 0 <= selected_index < len(files):
                selected_file_name = files[selected_index]
                self.selected_file = self.os.path.join(directory, selected_file_name)
                print(f"You have selected: {selected_file_name}")
                return self.selected_file
            else:
                print("Invalid file number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
        return None

    def get_modded_files_for_batch(self):
        modded_files = self.os.listdir(self.modded_directory)
        num_files = len(modded_files)
        if num_files == 0:
            print("No files found in the modded_data folder.")
            return None
        returning = []
        for file in modded_files:
            file_path = self.os.path.join(self.modded_directory, file)
            returning.append(file_path)

        return returning

    def get_raw_files_for_batch(self):
        raw_files = self.os.listdir(self.raw_directory)
        num_files = len(raw_files)
        if num_files == 0:
            print("No files found in the raw_data folder.")
            return None
        returning = []
        for file in raw_files:
            file_path = self.os.path.join(self.raw_directory, file)
            returning.append(file_path)

        return returning

    # def set_raw_files_for_batch(self):

    def continue_operations_with_modded_file(self):
        cont = self.misc.nli(
            "Would you like to continue operations with the modded version of this file"
        )
        if cont in self.misc.yes_array:
            self.selected_file
        pass

    def save_file_to_clean_dir(self):
        pass

    def read_csv_and_prepare_df(self, csv_file_path):
        # Read the CSV file into a DataFrame
        self.selected_file = csv_file_path
        df = self.pd.read_csv(csv_file_path)
        return df

    def show_df(self, df):
        # Print the resulting DataFrame
        print(df)

    # def create_or_update_modded_version(self, df):
    #     # Get the file name without the path
    #     file_name = self.os.path.basename(self.selected_file)
    #     # input("a")

    #     # Create the modded_data directory if it doesn't exist
    #     self.os.makedirs(self.modded_directory, exist_ok=True)
    #     # input("b")

    #     # Save the modified DataFrame as a CSV file in the modded_data directory
    #     modded_file_path = self.os.path.join(self.modded_directory, file_name)
    #     # input("c" + modded_file_path)
    #     df.to_csv(modded_file_path, index=False)
    #     # input("d")

    #     # Set the modded file as the new selected file
    #     self.selected_file = modded_file_path
    #     return self.selected_file

    def move_modded_to_clean_on_continuous_batch_completion(self):
        should_move = self.misc.nli(
            "Move files to clean directory?\nType 'y' for yes, otherwise press enter."
        )
        if should_move in self.misc.yes_array:
            # Select files to move
            files_to_move = self.get_modded_files_for_batch()
            # input(files_to_move)

            # Move files
            for file in files_to_move:
                destination = self.clean_directory
                print(f"MOVING {file} to {destination}")
                print(destination)

                try:
                    # Moves to designated location and replaces file if it already exists.
                    # self.shutil.move(file, destination, copy_function=self.shutil.copy2)
                    self.os.replace(
                        file,
                        self.os.path.join(destination, self.os.path.basename(file)),
                    )
                    print(f"Moved file '{file}' to {destination}")
                except Exception as e:
                    print(f"Error moving file '{file}': {str(e)}")

    def save_df_as_csv(self, df, selected_file, new_location):
        # Get the file name
        file_name = selected_file.rpartition("\\")[2]

        # Save the DataFrame as a CSV file
        if new_location == self.clean_directory:
            saved_file_location = self.os.path.join(self.clean_directory, file_name)
        elif new_location == self.modded_directory:
            saved_file_location = self.os.path.join(self.modded_directory, file_name)

        df.to_csv(f"{saved_file_location}", index=False)

        msg = f"Saved file to: {saved_file_location}. Press enter."

        return saved_file_location, msg

    def create_clean_version(self, df):
        # Get the file name without the path
        file_name = self.os.path.basename(self.selected_file)
        # input("a")

        # Create the modded_data directory if it doesn't exist
        self.os.makedirs(self.clean_directory, exist_ok=True)
        # input("b")

        # Save the modified DataFrame as a CSV file in the modded_data directory
        modded_file_path = self.os.path.join(self.modded_directory, file_name)
        # input("c" + modded_file_path)
        df.to_csv(modded_file_path, index=False)
        # input("d")

        # Set the modded file as the new selected file
        self.selected_file = modded_file_path
        return self.selected_file

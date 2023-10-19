# Copyright (c) 2023 Jarid Prince
import sys


class ChoiceViewer:
    def __init__(self, misc, ef, tf, lf, file_handler):
        self.misc = misc
        self.selected_category = None
        self.available_names_for_selected_category = []
        self.available_functions_for_category = []
        self.selected_function_in_category = None
        self.file_handler = file_handler

        self.ef = ef
        self.tf = tf
        self.lf = lf

    # Displays functions available for the selected choice
    def display_functions_for_choice(self):
        if self.selected_category == 1:
            self.available_names_for_selected_category = [
                f"({function_number + 1}) {function['name']}"
                for function_number, function in enumerate(self.ef)
            ]
        elif self.selected_category == 2:
            self.available_names_for_selected_category = [
                f"({function_number + 1}) {function['name']}"
                for function_number, function in enumerate(self.tf)
            ]
        elif self.selected_category == 3:
            self.available_names_for_selected_category = [
                f"({function_number + 1}) {function['name']}"
                for function_number, function in enumerate(self.lf)
            ]

        # self.misc.cls()
        while (
            not type(self.selected_function_in_category) is int
            or type(self.selected_function_in_category) is int
            and self.selected_function_in_category < 1
        ):
            self.kawaii_print(self.available_names_for_selected_category)
            try:
                self.selected_function_in_category = self.misc.nli(
                    "To select a function, type the corresponding number and press Enter. Press Enter to return to the previous screen.\n"
                )
            except KeyboardInterrupt:
                self.misc.nls("Exiting...")
                sys.exit()

            if self.selected_function_in_category == "":
                # print("returning true")
                return True

            else:
                try:
                    selected_function_index = (
                        int(self.selected_function_in_category) - 1
                    )

                    if selected_function_index < len(
                        self.available_functions_for_category
                    ):
                        selected_function = self.available_functions_for_category[
                            selected_function_index
                        ]
                        if selected_function is not None:
                            # self.misc.cls()
                            selected_function()  # Call the function directly
                            if (
                                not self.file_handler.selected_file == None
                                and not self.file_handler.selected_file == ""
                            ):
                                self.misc.nli(
                                    f"Using {self.file_handler.selected_file} Press Enter to continue..."
                                )
                            else:
                                self.misc.nli("Press Enter to continue...")
                            return True
                    else:
                        self.misc.nls("Returning to choice selection...")
                        self.selected_function_in_category = None
                        return False

                except Exception as e:
                    # self.misc.cls()
                    print(e)
                    self.misc.nls(
                        "You must type a number in the range. Try again or q to quit."
                    )
                    self.selected_function_in_category = ""

    # Displays options available for ETL, selection based on user input
    def check_view_input(self):
        option_choice = ""
        while (
            not type(option_choice) is int
            or type(option_choice) is int
            and option_choice > 3
            or type(option_choice) is int
            and option_choice < 1
        ):
            try:
                print("Pick a category for operations:")
                option_choice = self.misc.nli(
                    f"(1) Extract\n(2) Transform\n(3) Load\n\n{self.misc.bcolors.OKBLUE}Select an option to see functions to run.\nType 1, 2, or 3:\n{self.misc.bcolors.ENDC}"
                )
            except KeyboardInterrupt:
                self.misc.nls("Exiting...")
                sys.exit()
            if option_choice == "q":
                sys.exit()
            try:
                option_choice = int(option_choice)
            except:
                # self.misc.cls()
                # print(e)
                self.misc.nls(
                    "You must type a number in the range 1-3. Try again or q to quit."
                )
                option_choice = ""

        if option_choice == 1:
            self.available_functions_for_category = [
                func["function"] for func in self.ef
            ]
        elif option_choice == 2:
            self.available_functions_for_category = [
                func["function"] for func in self.tf
            ]
        elif option_choice == 3:
            self.available_functions_for_category = [
                func["function"] for func in self.lf
            ]

        self.selected_category = option_choice
        # self.display_functions_for_choice()

    # Neatly presents the function names in columns/rows by assessing the length of words to determine padding
    def kawaii_print(self, lst):
        num_columns = (len(lst) + 3) // 4
        num_rows = 4

        # Create a 2D list to store the function names in the desired format
        new_list = [
            lst[num * num_rows : (num + 1) * num_rows] for num in range(num_columns)
        ]

        if not lst:
            print("No functions available.")
            return

        col_width = max(len(word) for row in new_list for word in row) + 4  # padding

        self.misc.nls(
            f"{self.misc.bcolors.OKGREEN}FUNCTIONS AVAILABLE IN CHOICE:{self.misc.bcolors.ENDC}"
        )
        print(
            f"\n{self.misc.bcolors.OKBLUE}Select a function from below to run it.\n{self.misc.bcolors.ENDC}"
        )
        for row in range(num_rows):
            for col in range(num_columns):
                if row < len(new_list[col]):
                    word = new_list[col][row]
                    print(
                        f"{self.misc.bcolors.OKCYAN}{word.ljust(col_width)}{self.misc.bcolors.ENDC}",
                        end="",
                    )
            print()

# Copyright (c) 2023 Jarid Prince

import os, sys, traceback, re


class ChoiceLauncher:
    def __init__(self, misc, choice_viewer):
        self.misc = misc
        self.choice_viewer = choice_viewer
        self.choice_id = None
        self.selected = None

    def set_choice(self, choice):
        self.choice_id = int(choice)
        self.selected = f"day{str(choice)}"

    def launch(self):
        print(f"SELECTED: {self.selected}")
        print(f"ID: {str(self.choice_id)}")
        try:
            selected_functions = self.choice_viewer.selected_option_functions
            if self.choice_id <= len(selected_functions):
                selected_function = selected_functions[self.choice_id - 1]["function"]
                if selected_function is not None and callable(selected_function):
                    print(f"{selected_function}")
                    selected_function()
                else:
                    print("Invalid function.")

        except KeyboardInterrupt:
            self.misc.nls("Exiting...")
            sys.exit()
        except Exception as e:
            print(e)


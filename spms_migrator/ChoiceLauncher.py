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

            # # self.misc.cls()
            # self.misc.nls(f"{'*'*20} ERR! {'*'*20}\n")

            # dir_path = os.path.dirname(os.path.realpath(__file__))
            # exc_type, exc_obj, exc_tb = sys.exc_info()
            # fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            # # excdata = (traceback.extract_tb(exc_tb))
            # # excdata = (traceback.print_stack())

            # tbLines = traceback.format_exception(*sys.exc_info())
            # f = "\n"
            # # print(tbLines)
            # for l in tbLines[:-1]:
            #     if l == "Traceback (most recent call last):\n":
            #         #  or l == '  File "D:\\dev\\py100\\tools\\ProgramLauncher.py", line 122, in launch\n    self.DAYS[self.program_id - 1]()\n'
            #         pass
            #     else:
            #         l = str(l)
            #         l.lstrip().rstrip().replace("\n", "#\n").replace(" ", "")
            #         # print(l)

            #         f += l
            # f.lstrip().rstrip().replace("\n", "giggity")
            # raw = re.sub(r"File \"D:\\dev\\py100\\tools\\days\\day_0\d+", "", f)
            # raw = re.sub(r"\\main.py\", ", "", raw)
            # raw = re.sub(r", in day_0\d+", " in main", raw)
            # raw = re.sub(r"\\files\\", "", raw)
            # raw = re.sub(r".py\",", " @", raw)

            # print(
            #     f"{self.misc.bcolors.FAIL}FROM DIRECTORY:\t\t {dir_path}\{fname}@{exc_tb.tb_lineno}{self.misc.bcolors.ENDC}\n"
            # )
            # print(f"{self.misc.bcolors.FAIL}INFO:\n{raw}{self.misc.bcolors.ENDC}\n")
            # print(
            #     f"{self.misc.bcolors.HEADER}{exc_type.__name__.upper()}:\t\t {exc_obj}{self.misc.bcolors.ENDC}\n"
            # )

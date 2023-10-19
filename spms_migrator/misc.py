# Copyright (c) 2023 Jarid Prince

import os, sys


class bcolors:
    HEADER = "\033[95m"
    OKBLUE = "\033[94m"
    OKCYAN = "\033[96m"
    OKGREEN = "\033[92m"
    WARNING = "\033[93m"
    FAIL = "\033[91m"
    ENDC = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"


def nls(string_input):
    formatted_string = f"\n{string_input}\n"
    print(formatted_string)


def nli(string_input):
    fsi = input(f"\n{string_input}\n")
    return fsi


def title(string):
    ft = f'{bcolors.OKGREEN}\n{"*"*62}{bcolors.ENDC}\n\n\t\t\t{string}\n\n{bcolors.OKGREEN}\n{"*"*62}{bcolors.ENDC}\n'
    cls()
    print(ft)


def cls():
    os.system("clear")


def press_start():
    a = input("Press enter to start.")
    return a


yes_array = ["Yeah", "yeah", "Yea", "yea", "Ye", "ye", "Y", "y", "Yes", "yes"]
no_array = ["Nah", "nah", "Nay", "nay", "Na", "na", "N", "n", "No", "no"]

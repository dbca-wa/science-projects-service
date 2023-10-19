from ChoiceViewer import ChoiceViewer
from ChoiceLauncher import ChoiceLauncher
from FileHandler import FileHandler
from Extractor import Extractor
from Transformer import Transformer
from Loader import Loader
import pandas as pd
from tqdm import tqdm
import sys, os, psycopg2
import gc
import misc
from dotenv import load_dotenv


class Migrator:
    def __init__(self):
        self.main_looping = True
        self.choice_viewer = None
        self.choice_launcher = None
        self.file_handler = None
        self.extractor = None
        self.transformer = None
        self.loader = None
        self.extraction_functions = None
        self.transformation_functions = None
        self.loading_functions = None
        self.project = "SPMS"

        self.parent_directory = os.path.abspath(os.path.join(os.getcwd(), os.pardir))

    def instantiate_classes(self):
        self.file_handler = (
            FileHandler(
                project=self.project,
                pd=pd,
                os=os,
                misc=misc,
                # shutil=shutil,
                tqdm=tqdm,
            )
            if self.file_handler == None
            else self.file_handler
        )
        self.extractor = Extractor(
            file_handler=self.file_handler,
            misc=misc,
            tqdm=tqdm,
            pd=pd,
            os=os,
        )
        self.transformer = Transformer(
            file_handler=self.file_handler,
            misc=misc,
            tqdm=tqdm,
            pd=pd,
        )
        self.loader = Loader(
            file_handler=self.file_handler,
            misc=misc,
            tqdm=tqdm,
            pd=pd,
            psycopg2=psycopg2,
            os=os,
            load_dotenv=load_dotenv,
            parent_directory=self.parent_directory,
        )
        self.extraction_functions = self.extractor.functions
        self.transformation_functions = self.transformer.functions
        self.loading_functions = self.loader.functions
        self.choice_viewer = ChoiceViewer(
            misc,
            ef=self.extraction_functions,
            tf=self.transformation_functions,
            lf=self.loading_functions,
            file_handler=self.file_handler,
        )
        self.choice_launcher = ChoiceLauncher(misc, self.choice_viewer)

    def main_loop(self):
        self.instantiate_classes()
        self.choice_launcher.choice_viewer.check_view_input()
        self.main_looping = (
            self.choice_launcher.choice_viewer.display_functions_for_choice()
        )
        self.clean_up()

    def clean_up(self):
        del self.choice_launcher
        del self.choice_viewer
        # del self.file_handler
        del self.extractor
        del self.transformer
        del self.loader
        self.extraction_functions = None
        self.transformation_functions = None
        self.loading_functions = None
        gc.collect()


if __name__ == "__main__":
    misc.title(f"{misc.bcolors.WARNING}SPMS Migrator{misc.bcolors.ENDC}")
    print(
        f"{misc.bcolors.HEADER}IMPORTANT: Please make sure you are in the correct directory for this file.{misc.bcolors.ENDC}"
    )
    migrator = Migrator()
    while migrator.main_looping:
        migrator.main_loop()
    print("Exiting...")

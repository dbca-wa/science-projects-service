import csv
import os
import re
import subprocess
import psycopg2
import chardet


class Extractor:
    def __init__(self, file_handler, misc, tqdm, pd, os):
        self.conn = None
        self.pd = pd
        self.os = os
        self.tqdm = tqdm
        self.misc = misc
        self.file_handler = file_handler
        self.functions = [
            {
                "name": "Extract CSVs from Dump File",
                "function": self.run_it,
            },
        ]

    def create_temp_db(self):
        dbname = "sdis"
        password = "sdis"
        self.os.environ["PGPASSWORD"] = password

        # Run the createdb command
        print("Running create command")
        try:
            createdb_command = f"createdb --username=postgres --no-password {dbname}"
            subprocess.run(createdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run create command{self.misc.bcolors.ENDC}",
                e,
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DB Created successfully{self.misc.bcolors.ENDC}"
            )

    def drop_temp_db(self):
        dbname = "sdis"
        password = "sdis"
        self.os.environ["PGPASSWORD"] = password

        try:
            dropdb_command = (
                f"dropdb --if-exists --username=postgres --no-password {dbname}"
            )
            subprocess.run(dropdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run drop command{self.misc.bcolors.ENDC}",
                e,
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}DB Dropped successfully{self.misc.bcolors.ENDC}"
            )

    def connect_to_db(self):
        print("Establishing conn...")
        connection = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="sdis",
            user="azure_superuser",
            password="sdis",
        )

        # Create a cursor object to execute SQL queries
        print("Creating cursor")
        cursor = connection.cursor()

        # Ensuring encoding
        print("Ensuring encoding set to UTF8")
        cursor.execute("SET client_encoding = 'UTF8';")
        connection.commit()

        return connection, cursor

    # def cleanup(self):
    #     if self.conn:
    #         self.conn.close()

    def run_it(self):
        print(
            "use newextractor.py from within a spms docker container after pg_restoring the dump file"
        )

    #     self.drop_temp_db()
    #     self.create_temp_db()
    #     (connection, cursor) = self.connect_to_db()

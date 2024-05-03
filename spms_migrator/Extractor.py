import subprocess
import psycopg2
import os
import subprocess
import csv
import shutil


# Creates a temporary database, loads it with a dump file, extracts the data as csv tables
# and outputs it to a given directory (to be later used by Transformer and Loader classes)
class Extractor:
    def __init__(self, file_handler, misc, tqdm, pd, os):
        self.host = "localhost"
        self.port = 5432
        self.temp_db_name = "temp_db"
        self.temp_db_user = "postgres"
        self.temp_db_pass = "123"
        self.dump_file = os.path.join(os.getcwd(), "migration_dump.dump")
        self.output_directory = os.path.join(os.getcwd(), "csv_files")
        self.final_destination = os.path.join(os.getcwd(), "data", "raw_data")

        self.conn = None
        self.cursor = None
        self.pd = pd
        self.os = os
        self.tqdm = tqdm
        self.misc = misc
        self.file_handler = file_handler
        self.functions = [
            {
                "name": "Run All",
                "function": self.run_it,
            },
            {
                "name": "Create Temp DB",
                "function": self.create_temp_db,
            },
            {
                "name": "Connect to Temp DB",
                "function": self.connect_to_temp_db_and_ensure_encoding,
            },
            {
                "name": "Restore Dump to Temp DB",
                "function": self.restore_dump,
            },
            {
                "name": "Extract CSVs from Temp DB",
                "function": self.extract_data_to_csv,
            },
            {
                "name": "Drop Temp DB",
                "function": self.drop_temp_db,
            },
            {
                "name": "Copy CSVs to Raw Data Folder",
                "function": self.copy_files_to_raw_data_folder,
            },
        ]

    # 1
    def create_temp_db(self):
        dbname = self.temp_db_name
        passw = self.temp_db_pass
        self.os.environ["PGPASSWORD"] = passw

        # Run the createdb command
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Creating temp db...{self.misc.bcolors.ENDC}"
        )

        try:
            createdb_command = (
                f"createdb --username={self.temp_db_user} --no-password {dbname}"
            )
            subprocess.run(createdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run create command{self.misc.bcolors.ENDC}",
                e,
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}1/6) DB Created successfully!{self.misc.bcolors.ENDC}"
            )

    # 2
    def connect_to_temp_db_and_ensure_encoding(self):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Connecting to temporary database...{self.misc.bcolors.ENDC}"
        )
        try:
            connection = psycopg2.connect(
                host=self.host,
                port=self.port,
                database=self.temp_db_name,
                user=self.temp_db_user,  # Change this to a suitable temporary user
                password=self.temp_db_pass,  # Change this to a suitable temporary password
            )
            cursor = connection.cursor()
            # Ensuring encoding
            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Ensuring encoding set to UTF8...{self.misc.bcolors.ENDC}"
            )
            cursor.execute("SET client_encoding = 'UTF8';")
            connection.commit()

        except Exception as e:
            self.misc.nls(
                f"{self.misc.bcolors.FAIL}Error connecting to temp db and setting encoding: {e}{self.misc.bcolors.ENDC}"
            )
            raise
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}2/6) Connected to temp db and set encoding successfully!{self.misc.bcolors.ENDC}"
            )

        return connection, cursor

    # 3
    def restore_dump(self):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Restoring dump to temp db, please be patient...{self.misc.bcolors.ENDC}"
        )
        try:
            subprocess.run(
                [
                    "pg_restore",
                    "--no-owner",
                    f"--dbname={self.temp_db_name}",
                    self.dump_file,
                ]
            )
        except Exception as e:
            self.misc.nls(
                f"{self.misc.bcolors.FAIL}Error restoring dump to temp db: {e}{self.misc.bcolors.ENDC}"
            )
            raise
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}3/6) Dump restored to temp db successfully!{self.misc.bcolors.ENDC}"
            )

    # 4
    def extract_data_to_csv(self):
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Extracting CSVs, please be patient...{self.misc.bcolors.ENDC}"
        )
        # Loop over the tables and extract data from each table
        try:
            cursor = self.cursor
            # Get the list of tables in the database
            cursor.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
            )
            tables = cursor.fetchall()
            for table in tables:
                table_name = table[0]
                print(table_name)
                query = "SELECT * FROM {};".format(table_name)
                cursor.execute(query)
                rows = cursor.fetchall()

                # Write the data to a CSV file
                file_path = "{}/{}.csv".format(self.output_directory, table_name)
                print(file_path)
                # skip existing files
                if os.path.exists(file_path):
                    print("EXISTS, skipping...")
                    continue
                else:
                    with open(file_path, "w+", encoding="utf-8", newline="") as csvfile:
                        writer = csv.writer(csvfile)
                        writer.writerow(
                            [i[0] for i in cursor.description]
                        )  # Write headers
                        for row in rows:
                            writer.writerow(row)

        except Exception as e:
            self.misc.nls(
                f"{self.misc.bcolors.FAIL}Could not Extract CSV tables: {e}{self.misc.bcolors.ENDC}"
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}4/6) CSV Tables extracted successfully!{self.misc.bcolors.ENDC}"
            )

    # 5
    def drop_temp_db(self):
        dbname = self.temp_db_name
        if not self.os.environ["PGPASSWORD"]:
            self.os.environ["PGPASSWORD"] = self.temp_db_pass

        try:
            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Dropping Temp DB...{self.misc.bcolors.ENDC}"
            )
            self.conn.close()
            dropdb_command = f"dropdb --if-exists --username={self.temp_db_user} --no-password {dbname}"
            subprocess.run(dropdb_command, shell=True)
        except Exception as e:
            self.misc.nli(
                f"{self.misc.bcolors.FAIL}Could not Run drop command {e}{self.misc.bcolors.ENDC}"
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}5/6) DB Dropped successfully!{self.misc.bcolors.ENDC}"
            )

    # 6
    def copy_files_to_raw_data_folder(self):
        FOLDER_WITH_ITEMS = self.output_directory
        FOLDER_TO_MOVE_TO = self.final_destination

        try:
            self.misc.nls(
                f"{self.misc.bcolors.WARNING}Copying files to raw_data folder...{self.misc.bcolors.ENDC}"
            )
            # Remove existing items in the destination folder
            if os.path.exists(FOLDER_TO_MOVE_TO):
                shutil.rmtree(FOLDER_TO_MOVE_TO)

            # Recreate the destination folder
            os.makedirs(FOLDER_TO_MOVE_TO)

            # Iterate over files in the source directory
            for filename in os.listdir(FOLDER_WITH_ITEMS):
                if filename.endswith(".csv"):  # Check if the file is a CSV file
                    source_file = os.path.join(FOLDER_WITH_ITEMS, filename)
                    destination_file = os.path.join(FOLDER_TO_MOVE_TO, filename)

                    # Copy the file to the destination folder
                    shutil.copyfile(source_file, destination_file)

        except Exception as e:
            self.misc.nls(
                f"{self.misc.bcolors.FAIL}Could not Copy CSVs to raw_data folder {e}{self.misc.bcolors.ENDC}"
            )
        else:
            self.misc.nls(
                f"{self.misc.bcolors.OKGREEN}6/6) CSVs copied to raw_data folder!{self.misc.bcolors.ENDC}"
            )

    def run_it(self):
        # 1 Create temp DB
        self.create_temp_db()

        # 2 and Connect to it
        (connection, cursor) = self.connect_to_temp_db_and_ensure_encoding()
        self.conn = connection
        self.cursor = cursor

        # 3 Restore dump file
        self.restore_dump()

        # 4 Extract CSV files
        self.extract_data_to_csv()

        # 5 Drop the temp db
        self.drop_temp_db()

        # 6) copy files from csv_files to raw_data location for manipulation
        self.copy_files_to_raw_data_folder()

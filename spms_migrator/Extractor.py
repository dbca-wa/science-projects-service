import csv
import subprocess
import psycopg2


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
        dbname = "tempdb"
        password = "123"
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
        dbname = "tempdb"
        password = "123"
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

    def load_dump_directly_to_db(self, dump_file_path):
        # Connect to the temporary database
        self.conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="temp_db",
            user="postgres",
            password="123",
        )

        cursor = self.conn.cursor()

        # Read the dump file
        with open(dump_file_path, "r", encoding="iso-8859-1") as f:
            dump = f.read()

        # Execute the dump file as a single statement
        try:
            cursor.execute(dump)
            self.conn.commit()
            print("Dump file loaded successfully.")
        except psycopg2.Error as e:
            print("A database error occurred:", str(e))
            self.conn.rollback()

        cursor.close()

    def extract_data_to_csv(self, cursor, output_directory):
        # Get the list of tables in the database
        cursor.execute(
            "SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';"
        )
        tables = cursor.fetchall()

        # Loop over the tables and extract data from each table
        for table in tables:
            table_name = table[0]
            query = f"SELECT * FROM {table_name};"
            cursor.execute(query)
            rows = cursor.fetchall()

            # Write the data to a CSV file
            with open(
                f"{output_directory}/{table_name}.csv", "w", newline=""
            ) as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow([i[0] for i in cursor.description])  # Write headers
                for row in rows:
                    writer.writerow(row)

    def cleanup(self):
        if self.conn:
            self.conn.close()

    def run_it(self):
        print("Starting extract function")

        # Step 1: Define the paths
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Defining paths...{self.misc.bcolors.ENDC}"
        )
        dump_file_path = "./sdis.dump"
        output_directory = "./extracted_from_dump"

        # Step 2: Create temp db and Load the dump file into the temporary database
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Creating and connecting to Temp DB...{self.misc.bcolors.ENDC}"
        )

        print("Dropping temp DB if it exists...")
        self.drop_temp_db()

        print("Creating temp DB ...")
        self.create_temp_db()

        print("Connecting to temporary database...")

        self.conn = psycopg2.connect(
            host="127.0.0.1",
            port="5432",
            database="temp_db",
            user="postgres",
            password="123",
        )

        cursor = self.conn.cursor()

        print("Loading dump file into the temporary database...")

        subprocess.run(
            [
                "pg_restore",
                "--dbname=temp_db",
                "--username=postgres",
                "--no-owner",
                "--no-privileges",
                "--no-comments",
                "--clean",
                dump_file_path,
            ],
            check=True,
        )

        # Step 5: Extract and export to CSV files
        print("Extracting data to CSV files...")
        self.extract_data_to_csv(cursor=cursor, output_directory=output_directory)

        # Step 3: Cleanup
        self.misc.nls(
            f"{self.misc.bcolors.WARNING}Cleaning Up...{self.misc.bcolors.ENDC}"
        )
        self.cleanup()

        # Step 4: Drop the temporary database
        # self.misc.nls(
        #     f"{self.misc.bcolors.WARNING}Dropping DB...{self.misc.bcolors.ENDC}"
        # )
        # self.drop_temp_db()

        # # Step 3: Connect to temp db
        # self.misc.nls(
        #     f"{self.misc.bcolors.WARNING}Connecting to Temp DB...{self.misc.bcolors.ENDC}"
        # )
        # connection = psycopg2.connect(
        #     host="127.0.0.1",
        #     port="5432",
        #     database="temp_db",
        #     user="postgres",
        #     password="123",
        # )

        # cursor = connection.cursor()

        # # Step 4: Extract and export to CSV files
        # print("Creating Statements...")
        # with open(dump_file_path, "r", encoding="utf-8") as f:
        #     dump = f.read()
        # # with open(dump_file_path, "r", encoding="iso-8859-1") as f:
        # #     dump = f.read()
        # f.close()

        # statements = dump.split(";")

        # print("Creating Statements...")

        # with open("statements.sql", "w", encoding="utf-8") as txt:
        #     for statement in statements:
        #         txt.write(statement)
        #         txt.write(";")

        # txt.close()
        # try:
        #     print("Executing statements...")
        #     for statement in statements:
        #         print("Executing statement:", statement)
        #         cursor.execute(statement)

        #     print("Extracting to CSV...")
        #     self.extract_data_to_csv(cursor=cursor, output_directory=output_directory)

        #     # Step 5: Close the database connection
        #     print("Closing connection...")
        #     cursor.close()
        #     connection.close()

        #     # Step 6: Drop the temporary database
        #     self.drop_temp_db()

        # except psycopg2.Error as e:
        #     print("A database error occurred:", str(e))
        # except Exception as e:
        #     print("An unexpected error occurred during the extraction process:", str(e))
